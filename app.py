#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación Web Flask para Sistema de Reservas
Versión Modular - Reutiliza los módulos existentes
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import bcrypt
from datetime import datetime, date, timedelta
from db.connection import ejecutar_query, conectar
from mysql.connector import Error
from modules.validations import (
    validar_sancion, validar_limite_horas_dia, validar_limite_reservas_semana,
    validar_capacidad_sala, es_usuario_privilegiado, sala_compatible_usuario
)
import re
import os

app = Flask(__name__)
app.secret_key = 'reservas_salas_secret_key_2024'
app.config['JSON_AS_ASCII'] = False  # Para caracteres UTF-8 en JSON

# ============= CARGA DE CONSULTAS SQL =============

def cargar_consultas_sql(archivo='sql/consultas_reportes.sql'):
    """
    Carga las consultas SQL desde el archivo y las organiza por nombre.
    Retorna un diccionario con las consultas identificadas.
    """
    consultas = {}
    
    try:
        # Leer el archivo SQL
        ruta_archivo = os.path.join(os.path.dirname(__file__), archivo)
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Dividir por las secciones de CONSULTA
        secciones = re.split(r'-- =+\n-- CONSULTA (?:ADICIONAL )?(\d+):', contenido)
        
        # Procesar cada sección (van en pares: número y contenido)
        for i in range(1, len(secciones), 2):
            numero = secciones[i]
            bloque = secciones[i + 1] if i + 1 < len(secciones) else ''
            
            # Extraer la query SQL (después de los comentarios, hasta el siguiente --)
            sql_match = re.search(r'\n\n(SELECT.*?)(?=\n\n--|$)', bloque, re.DOTALL | re.IGNORECASE)
            if sql_match:
                query = sql_match.group(1).strip()
                
                # Limpiar la query: eliminar líneas en blanco y punto y coma final
                query = '\n'.join(line for line in query.split('\n') if line.strip())
                query = query.rstrip(';').strip()
                
                # Mapear a identificadores
                mapeo = {
                    '1': ('salas_mas_reservadas', query),
                    '2': ('turnos_demandados', query),
                    '3': ('promedio_participantes', query),
                    '4': ('reservas_por_carrera', query),
                    '5': ('ocupacion_edificio', query),
                    '6': ('reservas_por_tipo', query),
                    '7': ('sanciones_por_tipo', query),
                    '8': ('efectividad', query),
                    '9': ('horas_semana', query),
                    '10': ('participantes_sancionados', query),
                    '11': ('edificios_cancelaciones', query),
                }
                
                if numero in mapeo:
                    identificador, _ = mapeo[numero]
                    consultas[identificador] = query
        
        return consultas
    
    except FileNotFoundError:
        print(f"⚠️  Archivo {archivo} no encontrado")
        return {}
    except Exception as e:
        print(f"⚠️  Error al cargar consultas SQL: {e}")
        return {}


# Cargar las consultas al inicio
CONSULTAS_SQL = cargar_consultas_sql()

# ============= DECORADORES =============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Debes iniciar sesión para acceder.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Debes iniciar sesión para acceder.', 'warning')
            return redirect(url_for('login'))
        if not session.get('is_admin', False):
            flash('No tienes permisos de administrador.', 'danger')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ============= RUTAS PÚBLICAS =============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = ejecutar_query("SELECT * FROM login WHERE correo = %s", (email,), fetchone=True)
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['contrasena'].encode('utf-8')):
            session['user_email'] = email
            
            participante = ejecutar_query("SELECT * FROM participante WHERE email = %s", (email,), fetchone=True)
            
            if participante:
                session['user_ci'] = participante['ci']
                session['user_name'] = f"{participante['nombre']} {participante['apellido']}"
                
                es_docente = ejecutar_query(
                    "SELECT * FROM participante_programa_academico WHERE ci_participante = %s AND rol = 'docente'",
                    (participante['ci'],), fetchone=True
                )
                
                session['is_admin'] = bool(es_docente)
                flash(f'Bienvenido, {session["user_name"]}!', 'success')
                
                return redirect(url_for('admin_dashboard') if session['is_admin'] else url_for('user_dashboard'))
            else:
                flash('Usuario no encontrado en el sistema.', 'danger')
        else:
            flash('Credenciales incorrectas.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        ci = request.form.get('ci')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        programa = request.form.get('programa')
        rol = request.form.get('rol')
        
        if not all([ci, nombre, apellido, email, password, confirm_password, programa, rol]):
            flash('Todos los campos son obligatorios.', 'danger')
            programas = ejecutar_query("SELECT * FROM programa_academico ORDER BY nombre_programa", fetchall=True)
            return render_template('register.html', programas=programas)
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            programas = ejecutar_query("SELECT * FROM programa_academico ORDER BY nombre_programa", fetchall=True)
            return render_template('register.html', programas=programas)
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            programas = ejecutar_query("SELECT * FROM programa_academico ORDER BY nombre_programa", fetchall=True)
            return render_template('register.html', programas=programas)
        
        hash_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = conectar()
        if not conn:
            flash('Error de conexión con la base de datos.', 'danger')
            programas = ejecutar_query("SELECT * FROM programa_academico ORDER BY nombre_programa", fetchall=True)
            return render_template('register.html', programas=programas)
        
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO login (correo, contrasena) VALUES (%s, %s)", (email, hash_pass))
            cursor.execute("INSERT INTO participante (ci, nombre, apellido, email) VALUES (%s, %s, %s, %s)",
                          (ci, nombre, apellido, email))
            cursor.execute("""
                INSERT INTO participante_programa_academico (ci_participante, nombre_programa, rol)
                VALUES (%s, %s, %s)
            """, (ci, programa, rol))
            conn.commit()
            flash('Registro exitoso! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Error as e:
            conn.rollback()
            if 'Duplicate entry' in str(e):
                flash('El email o CI ya están registrados.', 'danger')
            else:
                flash(f'Error al registrar: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    programas = ejecutar_query("SELECT * FROM programa_academico ORDER BY nombre_programa", fetchall=True)
    return render_template('register.html', programas=programas)

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada exitosamente.', 'info')
    return redirect(url_for('index'))

# ============= PANEL DE USUARIO =============

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    reservas = ejecutar_query("""
        SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha, r.estado,
               CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
        WHERE rp.ci_participante = %s
        ORDER BY r.fecha DESC, t.hora_inicio DESC
        LIMIT 10
    """, (session['user_ci'],), fetchall=True)
    
    sancion = ejecutar_query("""
        SELECT * FROM sancion_participante
        WHERE ci_participante = %s AND CURDATE() BETWEEN fecha_inicio AND fecha_fin
    """, (session['user_ci'],), fetchone=True)
    
    return render_template('user/dashboard.html', reservas=reservas, sancion=sancion)

@app.route('/user/salas')
@login_required
def user_salas():
    salas = ejecutar_query("""
        SELECT s.nombre_sala, s.edificio, s.capacidad, s.tipo_sala, e.direccion
        FROM sala s
        JOIN edificio e ON s.edificio = e.nombre_edificio
        ORDER BY s.edificio, s.nombre_sala
    """, fetchall=True)
    return render_template('user/salas.html', salas=salas)

@app.route('/user/reservar', methods=['GET', 'POST'])
@login_required
def user_reservar():
    if request.method == 'POST':
        nombre_sala = request.form.get('nombre_sala')
        edificio = request.form.get('edificio')
        fecha_str = request.form.get('fecha')
        id_turno = request.form.get('id_turno')
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            id_turno = int(id_turno)
        except ValueError:
            flash('Datos inválidos.', 'danger')
            return redirect(url_for('user_reservar'))
        
        # Validaciones usando módulos existentes
        if not validar_sancion(session['user_ci']):
            return redirect(url_for('user_dashboard'))
        
        if not sala_compatible_usuario(nombre_sala, edificio, session['user_ci']):
            flash(f'No puedes reservar este tipo de sala.', 'danger')
            return redirect(url_for('user_reservar'))
        
        if not es_usuario_privilegiado(session['user_ci']):
            if not validar_limite_horas_dia(session['user_ci'], fecha, id_turno):
                return redirect(url_for('user_reservar'))
            if not validar_limite_reservas_semana(session['user_ci'], fecha):
                return redirect(url_for('user_reservar'))
        
        reserva_existente = ejecutar_query("""
            SELECT * FROM reserva WHERE nombre_sala = %s AND edificio = %s
            AND fecha = %s AND id_turno = %s
        """, (nombre_sala, edificio, fecha, id_turno), fetchone=True)
        
        if reserva_existente:
            flash('Este turno ya está reservado.', 'warning')
            return redirect(url_for('user_reservar'))
        
        conn = conectar()
        if not conn:
            flash('Error de conexión.', 'danger')
            return redirect(url_for('user_reservar'))
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reserva (nombre_sala, edificio, fecha, id_turno, estado)
                VALUES (%s, %s, %s, %s, 'activa')
            """, (nombre_sala, edificio, fecha, id_turno))
            
            id_reserva = cursor.lastrowid
            
            if not validar_capacidad_sala(nombre_sala, edificio, id_reserva, 1):
                conn.rollback()
                return redirect(url_for('user_reservar'))
            
            cursor.execute("""
                INSERT INTO reserva_participante (ci_participante, id_reserva)
                VALUES (%s, %s)
            """, (session['user_ci'], id_reserva))
            
            conn.commit()
            flash(f'Reserva #{id_reserva} creada exitosamente!', 'success')
            return redirect(url_for('user_dashboard'))
        except Error as e:
            conn.rollback()
            flash(f'Error al crear reserva: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    salas = ejecutar_query("SELECT * FROM sala ORDER BY edificio, nombre_sala", fetchall=True)
    turnos = ejecutar_query("SELECT * FROM turno ORDER BY hora_inicio", fetchall=True)
    return render_template('user/reservar.html', salas=salas, turnos=turnos, today=date.today().isoformat())

@app.route('/user/cancelar/<int:id_reserva>', methods=['POST'])
@login_required
def user_cancelar(id_reserva):
    reserva = ejecutar_query("""
        SELECT * FROM reserva_participante
        WHERE id_reserva = %s AND ci_participante = %s
    """, (id_reserva, session['user_ci']), fetchone=True)
    
    if not reserva:
        flash('Reserva no encontrada.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    resultado = ejecutar_query("UPDATE reserva SET estado = 'cancelada' WHERE id_reserva = %s",
                               (id_reserva,), commit=True)
    
    flash('Reserva cancelada exitosamente.' if resultado else 'Error al cancelar reserva.', 
          'success' if resultado else 'danger')
    return redirect(url_for('user_dashboard'))

# ============= PANEL DE ADMINISTRADOR =============

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'total_participantes': ejecutar_query("SELECT COUNT(*) as total FROM participante", fetchone=True)['total'],
        'total_salas': ejecutar_query("SELECT COUNT(*) as total FROM sala", fetchone=True)['total'],
        'reservas_activas': ejecutar_query("SELECT COUNT(*) as total FROM reserva WHERE estado = 'activa'", fetchone=True)['total'],
        'sanciones_activas': ejecutar_query("""
            SELECT COUNT(*) as total FROM sancion_participante
            WHERE CURDATE() BETWEEN fecha_inicio AND fecha_fin
        """, fetchone=True)['total']
    }
    
    reservas = ejecutar_query("""
        SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha, r.estado,
               CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario,
               COUNT(rp.ci_participante) as num_participantes
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        LEFT JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
        GROUP BY r.id_reserva ORDER BY r.fecha DESC, t.hora_inicio DESC LIMIT 10
    """, fetchall=True)
    
    return render_template('admin/dashboard.html', stats=stats, reservas=reservas)

@app.route('/admin/participantes')
@admin_required
def admin_participantes():
    participantes = ejecutar_query("""
        SELECT p.ci, p.nombre, p.apellido, p.email,
               GROUP_CONCAT(CONCAT(ppa.rol, ' en ', ppa.nombre_programa) SEPARATOR ', ') as programas
        FROM participante p
        LEFT JOIN participante_programa_academico ppa ON p.ci = ppa.ci_participante
        GROUP BY p.ci ORDER BY p.apellido, p.nombre
    """, fetchall=True)
    return render_template('admin/participantes.html', participantes=participantes)

@app.route('/admin/salas')
@admin_required
def admin_salas():
    salas = ejecutar_query("""
        SELECT s.nombre_sala, s.edificio, s.capacidad, s.tipo_sala, e.direccion
        FROM sala s JOIN edificio e ON s.edificio = e.nombre_edificio
        ORDER BY s.edificio, s.nombre_sala
    """, fetchall=True)
    return render_template('admin/salas.html', salas=salas)

@app.route('/admin/reservas')
@admin_required
def admin_reservas():
    reservas = ejecutar_query("""
        SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha,
               CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario, r.estado,
               COUNT(rp.ci_participante) as num_participantes
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        LEFT JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
        GROUP BY r.id_reserva ORDER BY r.fecha DESC LIMIT 100
    """, fetchall=True)
    return render_template('admin/reservas.html', reservas=reservas)

@app.route('/admin/sanciones')
@admin_required
def admin_sanciones():
    sanciones = ejecutar_query("""
        SELECT s.id_sancion, s.ci_participante, p.nombre, p.apellido,
               s.fecha_inicio, s.fecha_fin,
               CASE
                   WHEN CURDATE() BETWEEN s.fecha_inicio AND s.fecha_fin THEN 'ACTIVA'
                   WHEN CURDATE() > s.fecha_fin THEN 'FINALIZADA'
                   ELSE 'FUTURA'
               END as estado
        FROM sancion_participante s
        JOIN participante p ON s.ci_participante = p.ci
        ORDER BY s.fecha_inicio DESC
    """, fetchall=True)
    return render_template('admin/sanciones.html', sanciones=sanciones)

@app.route('/admin/reportes')
@admin_required
def admin_reportes():
    return render_template('admin/reportes.html')

@app.route('/admin/reportes/<tipo>')
@admin_required
def admin_reporte_data(tipo):
    """API para obtener datos de reportes - Queries desde archivo SQL"""
    
    # Verificar si el tipo de reporte existe
    if tipo not in CONSULTAS_SQL:
        print(f"⚠️ Reporte '{tipo}' no encontrado")
        print(f"Reportes disponibles: {list(CONSULTAS_SQL.keys())}")
        return jsonify({'error': f'Tipo de reporte no válido: {tipo}'}), 400
    
    # Ejecutar la consulta correspondiente
    try:
        query = CONSULTAS_SQL[tipo]
        print(f"\n🔍 Ejecutando reporte: {tipo}")
        print(f"Query: {query[:100]}...")  # Primeros 100 caracteres
        
        datos = ejecutar_query(query, fetchall=True)
        
        if datos is None:
            datos = []
        
        print(f"✅ Reporte ejecutado: {len(datos)} registros")
        return jsonify(datos if datos else [])
    except Exception as e:
        print(f"❌ Error ejecutando reporte {tipo}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error al ejecutar la consulta: {str(e)}'}), 500


@app.route('/admin/reportes/disponibles')
@admin_required
def admin_reportes_disponibles():
    """Retorna la lista de reportes disponibles"""
    reportes = [
        {'id': 'salas_mas_reservadas', 'nombre': 'Salas Más Reservadas', 'descripcion': 'Top 10 de salas con mayor demanda'},
        {'id': 'turnos_demandados', 'nombre': 'Turnos Más Demandados', 'descripcion': 'Horarios más solicitados'},
        {'id': 'promedio_participantes', 'nombre': 'Promedio de Participantes', 'descripcion': 'Ocupación promedio por sala'},
        {'id': 'reservas_por_carrera', 'nombre': 'Reservas por Carrera', 'descripcion': 'Distribución por programa académico'},
        {'id': 'ocupacion_edificio', 'nombre': 'Ocupación por Edificio', 'descripcion': 'Eficiencia de uso de espacios (últimos 30 días)'},
        {'id': 'reservas_por_tipo', 'nombre': 'Reservas por Tipo de Usuario', 'descripcion': 'Comparación docentes vs alumnos'},
        {'id': 'sanciones_por_tipo', 'nombre': 'Sanciones por Tipo de Usuario', 'descripcion': 'Comportamiento disciplinario por rol'},
        {'id': 'efectividad', 'nombre': 'Efectividad de Reservas', 'descripcion': 'Porcentaje de utilización vs cancelación'},
        {'id': 'horas_semana', 'nombre': 'Horas Reservadas por Semana', 'descripcion': 'Tendencias temporales (últimas 8 semanas)'},
        {'id': 'participantes_sancionados', 'nombre': 'Participantes Más Sancionados', 'descripcion': 'Top 10 usuarios con más sanciones'},
        {'id': 'edificios_cancelaciones', 'nombre': 'Edificios con Más Cancelaciones', 'descripcion': 'Problemas de infraestructura por ubicación'},
    ]
    return jsonify(reportes)


if __name__ == '__main__':
    # Mostrar consultas cargadas al iniciar
    print("\n🔍 Consultas SQL cargadas:")
    for key in CONSULTAS_SQL.keys():
        print(f"   ✓ {key}")
    print(f"\n📊 Total: {len(CONSULTAS_SQL)} reportes disponibles\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)