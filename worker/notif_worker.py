# worker/notif_worker.py  (versión corregida y más robusta)
import os
import time
import smtplib
import traceback
from email.message import EmailMessage
import mysql.connector
from mysql.connector import Error as MySQLError

# --- Config desde env ---
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'app_user'),
    'password': os.getenv('DB_PASS', 'app_pass'),
    'database': os.getenv('DB_NAME', 'reserva_salas'),
    'raise_on_warnings': True,
    'connection_timeout': 10
}

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.example.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', 'no-reply@example.com')
SMTP_PASS = os.getenv('SMTP_PASS', 'secret')
SMTP_FROM = os.getenv('SMTP_FROM', 'UCU <no-reply@ucu.edu.uy>')

WORKER_SLEEP = int(os.getenv('WORKER_SLEEP', '10'))
DRY_RUN = os.getenv('WORKER_DRY_RUN', 'true').lower() in ('1', 'true', 'yes')  # si true, no manda mails

# --- Helpers ---
def send_email_real(to_email, subject, body):
    """Enviar email real via SMTP; puede lanzar excepciones."""
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email
    msg.set_content(body)
    # conexión SMTP segura
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
        s.ehlo()
        # intentar STARTTLS si el servidor lo soporta
        try:
            s.starttls()
            s.ehlo()
        except Exception:
            # si falla starttls, seguimos intentando login (algunos servidores no lo requieren)
            pass
        if SMTP_USER and SMTP_PASS:
            s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

def send_email(to_email, subject, body):
    if DRY_RUN:
        # útil para pruebas locales sin SMTP
        print(f"[DRY_RUN] Enviar correo a: {to_email} | asunto: {subject}\n{body}\n")
        return
    return send_email_real(to_email, subject, body)

def compute_next_attempt_minutes(intentos, base_minutes=5, max_minutes=24*60):
    # backoff lineal (intentos * base) limitado a max_minutes
    m = intentos * base_minutes
    return min(m, max_minutes)

def process_row(conn, cur, r):
    id_notif = r['id_notif']
    destinatario = r.get('destinatario_email')
    intentos = r.get('intentos') or 0
    max_intentos = r.get('max_intentos') or 5
    asunto = r.get('asunto') or '(sin asunto)'
    cuerpo = r.get('cuerpo') or ''

    if not destinatario:
        cur.execute(
            "UPDATE notificacion SET estado=%s, last_error=%s, intentos=intentos+1 WHERE id_notif=%s",
            ('error', 'no email', id_notif)
        )
        conn.commit()
        print(f"[WARN] notificacion {id_notif} sin destinatario -> marcado error")
        return

    try:
        send_email(destinatario, asunto, cuerpo)
        cur.execute(
            "UPDATE notificacion SET estado=%s, enviado_at=NOW() WHERE id_notif=%s",
            ('enviado', id_notif)
        )
        conn.commit()
        print(f"[OK] notificacion {id_notif} enviada a {destinatario}")
    except Exception as e:
        err = str(e)
        intentos_new = intentos + 1
        if intentos_new >= max_intentos:
            # marcar como error permanente
            cur.execute(
                "UPDATE notificacion SET estado=%s, last_error=%s, intentos=%s WHERE id_notif=%s",
                ('error', err, intentos_new, id_notif)
            )
            conn.commit()
            print(f"[ERROR] notificacion {id_notif} -> alcanzó max_intentos ({max_intentos}). error: {err}")
        else:
            # programar reintento con backoff (minutos)
            wait_min = compute_next_attempt_minutes(intentos_new)
            cur.execute(
                "UPDATE notificacion SET intentos=%s, last_error=%s, next_intento_at=DATE_ADD(NOW(), INTERVAL %s MINUTE) WHERE id_notif=%s",
                (intentos_new, err, wait_min, id_notif)
            )
            conn.commit()
            print(f"[RETRY] notificacion {id_notif} -> intentos={intentos_new}. siguiente intento en {wait_min} min. error: {err}")

# --- Loop principal ---
print("Worker iniciado. DRY_RUN =", DRY_RUN)
while True:
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # aseguramos que autocommit está desactivado (vamos a controlar commits)
        conn.autocommit = False
        cur = conn.cursor(dictionary=True)

        # iniciar transacción explícita (necesario para SELECT ... FOR UPDATE)
        conn.start_transaction(isolation_level='READ COMMITTED')

        # seleccionar filas pendientes para procesar y bloquearlas
        cur.execute(
            "SELECT id_notif, destinatario_email, asunto, cuerpo, intentos, max_intentos "
            "FROM notificacion "
            "WHERE estado='pendiente' AND (next_intento_at IS NULL OR next_intento_at <= NOW()) "
            "ORDER BY creado_at ASC "
            "LIMIT 10 FOR UPDATE"
        )
        rows = cur.fetchall()

        if not rows:
            # no hay trabajos; limpiar y dormir
            cur.close()
            conn.close()
            time.sleep(WORKER_SLEEP)
            continue

        for r in rows:
            try:
                process_row(conn, cur, r)
            except Exception as inner_e:
                # si hay error inesperado por fila, registrarlo y continuar
                try:
                    cur.execute(
                        "UPDATE notificacion SET intentos=intentos+1, last_error=%s WHERE id_notif=%s",
                        (str(inner_e), r.get('id_notif'))
                    )
                    conn.commit()
                except Exception:
                    # si update falla, hacemos rollback para evitar lock corrupto
                    conn.rollback()
                print("[EXCEPCIÓN fila]", r.get('id_notif'), str(inner_e))
                traceback.print_exc()

        # cerramos cursor y conexión al terminar lote
        try:
            cur.close()
            conn.close()
        except Exception:
            pass

    except MySQLError as db_e:
        print("[Worker error - DB] ", str(db_e))
        traceback.print_exc()
        # si la conexión falla, dormir y reintentar
        try:
            if 'conn' in locals() and conn.is_connected():
                conn.close()
        except Exception:
            pass
        time.sleep(WORKER_SLEEP)
    except Exception as e:
        print("[Worker error - general]", str(e))
        traceback.print_exc()
        time.sleep(WORKER_SLEEP)
