# worker: procesa notificacion (simplificado)
import os, time, smtplib
from email.message import EmailMessage
import mysql.connector

DB_CONFIG = {
    'host': os.getenv('DB_HOST','localhost'),
    'user': os.getenv('DB_USER','app_user'),
    'password': os.getenv('DB_PASS','app_pass'),
    'database': os.getenv('DB_NAME','reserva_salas'),
    'autocommit': False
}

SMTP_HOST = os.getenv('SMTP_HOST','smtp.example.com')
SMTP_PORT = int(os.getenv('SMTP_PORT','587'))
SMTP_USER = os.getenv('SMTP_USER','no-reply@example.com')
SMTP_PASS = os.getenv('SMTP_PASS','secret')
SMTP_FROM = os.getenv('SMTP_FROM','UCU <no-reply@ucu.edu.uy>')
WORKER_SLEEP = int(os.getenv('WORKER_SLEEP', '10'))

def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)

while True:
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)
        cur.execute(\"SELECT * FROM notificacion WHERE estado='pendiente' AND (next_intento_at IS NULL OR next_intento_at <= NOW()) LIMIT 10 FOR UPDATE\")
        rows = cur.fetchall()
        for r in rows:
            try:
                if not r['destinatario_email']:
                    cur.execute(\"UPDATE notificacion SET estado='error', last_error=%s, intentos=intentos+1 WHERE id_notif=%s\", (\"no email\", r['id_notif']))
                    conn.commit()
                    continue
                send_email(r['destinatario_email'], r['asunto'], r['cuerpo'])
                cur.execute(\"UPDATE notificacion SET estado='enviado', enviado_at=NOW() WHERE id_notif=%s\", (r['id_notif'],))
                conn.commit()
            except Exception as e:
                cur.execute(\"UPDATE notificacion SET intentos=intentos+1, last_error=%s WHERE id_notif=%s\", (str(e), r['id_notif']))
                conn.commit()
        cur.close(); conn.close()
    except Exception as e:
        print('Worker error:', e)
    time.sleep(WORKER_SLEEP)
