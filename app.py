#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación Web Flask para Sistema de Reservas
Versión Completa con ABM + Reportes BI
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
from modules import participantes, salas, reservas, sanciones
import re
import os

app = Flask(__name__)
app.secret_key = 'reservas_salas_secret_key_2024'
app.config['JSON_AS_ASCII'] = False

# ============= CARGA DE CONSULTAS SQL =============

def cargar_consultas_sql(archivo='sql/consultas_reportes.sql'):
    """Carga las consultas SQL desde el archivo"""
    consultas = {}
    
    try:
        ruta_archivo = os.path.join(os.path.dirname(__file__), archivo)
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        secciones = re.split(r'-- =+\n-- CONSULTA (?:ADICIONAL )?(\d+):', contenido)
        
        for i in range(1, len(secciones), 2):
            numero = secciones[i]
            bloque = secciones[i + 1] if i + 1 < len(secciones) else ''
            
            sql_match = re.search(r'\n\n(SELECT.*?)(?=\n\n--|$)', bloque, re.DOTALL | re.IGNORECASE)
            if sql_match:
                query = sql_match.group(1).strip()
                query = '\n'.join(line for line in query.split('\n') if line.strip())
                query = query.rstrip(';').strip()
                
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
        
        exito, mensaje = participantes.crear_participante(ci, nombre, apellido, email, password, programa, rol)
        flash(mensaje, 'success' if exito else 'danger')
        
        if exito:
            return redirect(url_for('login'))
    
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
    reservas_list = reservas.obtener_reservas_participante(session['user_ci'])
    sancion = ejecutar_query("""
        SELECT * FROM sancion_participante
        WHERE ci_participante = %s AND CURDATE() BETWEEN fecha_inicio AND fecha_fin
    """, (session['user_ci'],), fetchone=True)
    
    return render_template('user/dashboard.html', reservas=reservas_list, sancion=sancion)

@app.route('/user/salas')
@login_required
def user_salas():
    salas_list = salas.obtener_salas()
    return render_template('user/salas.html', salas=salas_list)

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
        
        exito, mensaje, id_nueva_reserva = reservas.crear_reserva(nombre_sala, edificio, fecha, id_turno, session['user_ci'])
        
        if exito:
            if not validar_capacidad_sala(nombre_sala, edificio, id_nueva_reserva, 1):
                reservas.eliminar_reserva(id_nueva_reserva)
                return redirect(url_for('user_reservar'))
            
            flash(f'Reserva #{id_nueva_reserva} creada exitosamente!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash(mensaje, 'danger')
    
    salas_list = salas.obtener_salas()
    turnos_list = reservas.obtener_turnos()
    return render_template('user/reservar.html', salas=salas_list, turnos=turnos_list, today=date.today().isoformat())

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
    
    exito, mensaje = reservas.cancelar_reserva(id_reserva)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('user_dashboard'))

@app.route('/user/cambiar-password', methods=['GET', 'POST'])
@login_required
def user_cambiar_password():
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        password_actual = request.form.get('password_actual')
        password_nueva = request.form.get('password_nueva')
        password_confirmar = request.form.get('password_confirmar')
        
        user = ejecutar_query("SELECT * FROM login WHERE correo = %s", 
                             (session['user_email'],), fetchone=True)
        
        if not user or not bcrypt.checkpw(password_actual.encode('utf-8'), 
                                          user['contrasena'].encode('utf-8')):
            flash('Contraseña actual incorrecta', 'danger')
            return render_template('user/cambiar_password.html')
        
        if password_nueva != password_confirmar:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('user/cambiar_password.html')
        
        if len(password_nueva) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'danger')
            return render_template('user/cambiar_password.html')
        
        if participantes.actualizar_password(session['user_email'], password_nueva):
            flash('Contraseña actualizada exitosamente', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Error al actualizar contraseña', 'danger')
    
    return render_template('user/cambiar_password.html')

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
    
    reservas_list = ejecutar_query("""
        SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha, r.estado,
               CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario,
               COUNT(rp.ci_participante) as num_participantes
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        LEFT JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
        GROUP BY r.id_reserva ORDER BY r.fecha DESC, t.hora_inicio DESC LIMIT 10
    """, fetchall=True)
    
    return render_template('admin/dashboard.html', stats=stats, reservas=reservas_list)

# ========== PARTICIPANTES ==========

@app.route('/admin/participantes')
@admin_required
def admin_participantes():
    participantes_list = participantes.obtener_participantes()
    return render_template('admin/participantes.html', participantes=participantes_list)

@app.route('/admin/participantes/editar/<ci>', methods=['GET', 'POST'])
@admin_required
def admin_editar_participante(ci):
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        
        exito, mensaje = participantes.actualizar_participante(ci, nombre, apellido, email)
        flash(mensaje, 'success' if exito else 'danger')
        
        if exito:
            return redirect(url_for('admin_participantes'))
    
    participante = participantes.obtener_participante(ci)
    if not participante:
        flash('Participante no encontrado', 'danger')
        return redirect(url_for('admin_participantes'))
    
    programas = ejecutar_query("SELECT * FROM programa_academico ORDER BY nombre_programa", fetchall=True)
    return render_template('admin/editar_participante.html', participante=participante, programas=programas)

@app.route('/admin/participantes/eliminar/<ci>', methods=['POST'])
@admin_required
def admin_eliminar_participante(ci):
    exito, mensaje = participantes.eliminar_participante(ci)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_participantes'))

@app.route('/admin/participantes/<ci>/eliminar_programa/<programa>', methods=['POST'])
@admin_required
def admin_eliminar_programa(ci, programa):

    ejecutar_query("""
        DELETE FROM participante_programa_academico
        WHERE ci_participante = %s AND nombre_programa = %s
    """, (ci, programa), commit=True)

    flash("Programa eliminado correctamente", "success")
    return redirect(url_for('admin_editar_participante', ci=ci))

@app.route('/admin/participantes/<ci>/agregar_programa', methods=['POST'])
@admin_required
def admin_agregar_programa(ci):

    nombre_programa = request.form.get("nombre_programa")
    rol = request.form.get("rol")

    # Convertir rol para que coincida con MySQL
    if rol == "estudiante":
        rol = "alumno"

    if not nombre_programa or not rol:
        flash("Debe seleccionar programa y rol", "danger")
        return redirect(url_for('admin_editar_participante', ci=ci))

    ejecutar_query("""
        INSERT INTO participante_programa_academico (ci_participante, nombre_programa, rol)
        VALUES (%s, %s, %s)
    """, (ci, nombre_programa, rol), commit=True)

    flash("Programa agregado correctamente", "success")
    return redirect(url_for('admin_editar_participante', ci=ci))


# ========== SALAS ==========

@app.route('/admin/salas')
@admin_required
def admin_salas():
    salas_list = salas.obtener_salas()
    return render_template('admin/salas.html', salas=salas_list)

@app.route('/admin/salas/crear', methods=['GET', 'POST'])
@admin_required
def admin_crear_sala():
    if request.method == 'POST':
        nombre_sala = request.form.get('nombre_sala')
        edificio = request.form.get('edificio')
        capacidad = int(request.form.get('capacidad'))
        tipo_sala = request.form.get('tipo_sala')
        
        exito, mensaje = salas.crear_sala(nombre_sala, edificio, capacidad, tipo_sala)
        flash(mensaje, 'success' if exito else 'danger')
        
        if exito:
            return redirect(url_for('admin_salas'))
    
    edificios = salas.obtener_edificios()
    tipos_sala = salas.obtener_tipos_sala()
    return render_template('admin/crear_sala.html', edificios=edificios, tipos_sala=tipos_sala)

@app.route('/admin/salas/editar/<nombre_sala>/<edificio>', methods=['GET', 'POST'])
@admin_required
def admin_editar_sala(nombre_sala, edificio):
    if request.method == 'POST':
        nombre_sala_nuevo = request.form.get('nombre_sala')
        edificio_nuevo = request.form.get('edificio')
        capacidad = int(request.form.get('capacidad'))
        tipo_sala = request.form.get('tipo_sala')
        
        exito, mensaje = salas.actualizar_sala(nombre_sala, edificio, nombre_sala_nuevo, 
                                               edificio_nuevo, capacidad, tipo_sala)
        flash(mensaje, 'success' if exito else 'danger')
        
        if exito:
            return redirect(url_for('admin_salas'))
    
    sala = salas.obtener_sala(nombre_sala, edificio)
    if not sala:
        flash('Sala no encontrada', 'danger')
        return redirect(url_for('admin_salas'))
    
    edificios = salas.obtener_edificios()
    tipos_sala = salas.obtener_tipos_sala()
    stats = salas.obtener_estadisticas_sala(nombre_sala, edificio)
    
    return render_template('admin/editar_sala.html', sala=sala, edificios=edificios, 
                          tipos_sala=tipos_sala, stats=stats)

@app.route('/admin/salas/eliminar/<nombre_sala>/<edificio>', methods=['POST'])
@admin_required
def admin_eliminar_sala(nombre_sala, edificio):
    exito, mensaje = salas.eliminar_sala(nombre_sala, edificio)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_salas'))

# ========== EDIFICIO ==========

@app.route('/admin/crear_edificio', methods=['GET', 'POST'])
@admin_required
def admin_crear_edificio():
    if request.method == 'POST':
        nombre = request.form.get('nombre_edificio')
        direccion = request.form.get('direccion')

        ejecutar_query("""
            INSERT INTO edificio (nombre_edificio, direccion)
            VALUES (%s, %s)
        """, (nombre, direccion), commit=True)

        flash("Edificio creado correctamente", "success")
        return redirect(url_for('admin_salas'))

    return render_template('admin/crear_edificio.html')

# ========== RESERVAS ==========

@app.route('/admin/reservas')
@admin_required
def admin_reservas():
    reservas_list = reservas.obtener_reservas()
    return render_template('admin/reservas.html', reservas=reservas_list)

@app.route('/admin/reservas/editar/<int:id_reserva>', methods=['GET', 'POST'])
@admin_required
def admin_editar_reserva(id_reserva):
    if request.method == 'POST':
        nombre_sala = request.form.get('nombre_sala')
        edificio = request.form.get('edificio')
        fecha_str = request.form.get('fecha')
        id_turno = int(request.form.get('id_turno'))
        
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        exito, mensaje = reservas.actualizar_reserva(id_reserva, nombre_sala, edificio, fecha, id_turno)
        flash(mensaje, 'success' if exito else 'danger')
        
        if exito:
            return redirect(url_for('admin_reservas'))
    
    reserva = reservas.obtener_reserva(id_reserva)
    if not reserva:
        flash('Reserva no encontrada', 'danger')
        return redirect(url_for('admin_reservas'))
    
    salas_list = salas.obtener_salas()
    turnos_list = reservas.obtener_turnos()
    
    return render_template('admin/editar_reserva.html', reserva=reserva, 
                          salas=salas_list, turnos=turnos_list)

@app.route('/admin/reservas/<int:id_reserva>/estado', methods=['POST'])
@admin_required
def admin_cambiar_estado_reserva(id_reserva):
    nuevo_estado = request.form.get('estado')
    exito, mensaje = reservas.cambiar_estado_reserva(id_reserva, nuevo_estado)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_reservas'))

@app.route('/admin/reservas/eliminar/<int:id_reserva>', methods=['POST'])
@admin_required
def admin_eliminar_reserva(id_reserva):
    exito, mensaje = reservas.eliminar_reserva(id_reserva)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_reservas'))

@app.route('/admin/reservas/<int:id_reserva>/participantes', methods=['GET', 'POST'])
@admin_required
def admin_gestionar_participantes_reserva(id_reserva):

    # --- PROCESAR ACCIONES POST ---
    if request.method == 'POST':
        accion = request.form.get("accion")
        ci = request.form.get("ci_participante")

        # 1) AGREGAR PARTICIPANTE
        if accion == "agregar":
            ejecutar_query("""
                INSERT INTO reserva_participante (ci_participante, id_reserva, fecha_solicitud_reserva)
                VALUES (%s, %s, NOW())
            """, (ci, id_reserva), commit=True)

            flash("Participante agregado correctamente", "success")
            return redirect(url_for('admin_gestionar_participantes_reserva', id_reserva=id_reserva))

        # 2) ELIMINAR PARTICIPANTE
        if accion == "eliminar":
            ejecutar_query("""
                DELETE FROM reserva_participante
                WHERE ci_participante = %s AND id_reserva = %s
            """, (ci, id_reserva), commit=True)

            flash("Participante eliminado", "success")
            return redirect(url_for('admin_gestionar_participantes_reserva', id_reserva=id_reserva))

        # 3) MARCAR ASISTENCIA
        if accion == "asistencia":
            asistio = request.form.get("asistio")  # 1 o 0
            ejecutar_query("""
                UPDATE reserva_participante
                SET asistencia = %s
                WHERE ci_participante = %s AND id_reserva = %s
            """, (asistio, ci, id_reserva), commit=True)

            flash("Asistencia actualizada", "success")
            return redirect(url_for('admin_gestionar_participantes_reserva', id_reserva=id_reserva))

    # -------------------------------
    # --- OBTENER INFORMACIÓN GET ---
    # -------------------------------

    # Obtener reserva
    reserva = ejecutar_query("""
        SELECT 
            r.id_reserva,
            r.nombre_sala,
            r.edificio,
            r.fecha,
            CONCAT(t.hora_inicio, ' - ', t.hora_fin) AS horario,
            s.capacidad
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        JOIN sala s ON r.nombre_sala = s.nombre_sala AND r.edificio = s.edificio
        WHERE r.id_reserva = %s
    """, (id_reserva,), fetchone=True)

    if not reserva:
        flash("Reserva no encontrada", "danger")
        return redirect(url_for('admin_reservas'))

    # Participantes actuales
    participantes = ejecutar_query("""
        SELECT 
            p.ci AS ci_participante,
            p.nombre,
            p.apellido,
            p.email,
            rp.asistencia
        FROM reserva_participante rp
        JOIN participante p ON rp.ci_participante = p.ci
        WHERE rp.id_reserva = %s
    """, (id_reserva,), fetchall=True)

    reserva["participantes"] = participantes

    # Participantes disponibles
    participantes_disponibles = ejecutar_query("""
        SELECT ci, nombre, apellido
        FROM participante
        WHERE ci NOT IN (
            SELECT ci_participante
            FROM reserva_participante
            WHERE id_reserva = %s
        )
    """, (id_reserva,), fetchall=True)

    return render_template(
        'admin/gestionar_participantes_reserva.html',
        reserva=reserva,
        participantes_disponibles=participantes_disponibles
    )


@app.route('/admin/reservas/<int:id_reserva>/marcar_asistencia', methods=['POST'])
@admin_required
def admin_marcar_asistencia(id_reserva):
    ci = request.form.get('ci_participante')
    asistio = request.form.get('asistio')  # '1' o '0'

    if ci is None or asistio is None:
        flash("Datos inválidos", "danger")
        return redirect(url_for('admin_gestionar_participantes_reserva', id_reserva=id_reserva))

    ejecutar_query("""
        UPDATE reserva_participante
        SET asistencia = %s
        WHERE id_reserva = %s AND ci_participante = %s
    """, (asistio, id_reserva, ci))

    flash("Asistencia actualizada.", "success")
    return redirect(url_for('admin_gestionar_participantes_reserva', id_reserva=id_reserva))


# ========== SANCIONES ==========

@app.route('/admin/sanciones')
@admin_required
def admin_sanciones():
    sanciones_list = sanciones.obtener_sanciones()
    return render_template('admin/sanciones.html', sanciones=sanciones_list)

@app.route('/admin/sanciones/crear', methods=['GET', 'POST'])
@admin_required
def admin_crear_sancion():
    if request.method == 'POST':
        ci_participante = request.form.get('ci_participante')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        
        exito, mensaje, id_sancion = sanciones.crear_sancion(ci_participante, fecha_inicio, fecha_fin)
        flash(mensaje, 'success' if exito else 'danger')
        
        if exito:
            return redirect(url_for('admin_sanciones'))
    
    participantes_list = participantes.obtener_participantes()
    return render_template('admin/crear_sancion.html', participantes=participantes_list)

@app.route('/admin/sanciones/editar/<int:id_sancion>', methods=['GET', 'POST'])
@admin_required
def admin_editar_sancion(id_sancion):
    if request.method == 'POST':
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        
        exito, mensaje = sanciones.actualizar_sancion(id_sancion, fecha_inicio, fecha_fin)
        flash(mensaje, 'success' if exito else 'danger')
        
        if exito:
            return redirect(url_for('admin_sanciones'))
    
    sancion = sanciones.obtener_sancion(id_sancion)
    if not sancion:
        flash('Sanción no encontrada', 'danger')
        return redirect(url_for('admin_sanciones'))
    
    return render_template('admin/editar_sancion.html', sancion=sancion)

@app.route('/admin/sanciones/eliminar/<int:id_sancion>', methods=['POST'])
@admin_required
def admin_eliminar_sancion(id_sancion):
    exito, mensaje = sanciones.eliminar_sancion(id_sancion)
    flash(mensaje, 'success' if exito else 'danger')
    return redirect(url_for('admin_sanciones'))

# ========== REPORTES ==========

@app.route('/admin/reportes')
@admin_required
def admin_reportes():
    return render_template('admin/reportes.html')

@app.route('/admin/reportes/<tipo>')
@admin_required
def admin_reporte_data(tipo):
    if tipo not in CONSULTAS_SQL:
        print(f"⚠️ Reporte '{tipo}' no encontrado")
        return jsonify({'error': f'Tipo de reporte no válido: {tipo}'}), 400
    
    try:
        query = CONSULTAS_SQL[tipo]
        datos = ejecutar_query(query, fetchall=True)
        return jsonify(datos if datos else [])
    except Exception as e:
        print(f"❌ Error ejecutando reporte {tipo}: {e}")
        return jsonify({'error': f'Error al ejecutar la consulta: {str(e)}'}), 500

@app.route('/admin/reportes/disponibles')
@admin_required
def admin_reportes_disponibles():
    reportes_list = [
        {'id': 'salas_mas_reservadas', 'nombre': 'Salas Más Reservadas'},
        {'id': 'turnos_demandados', 'nombre': 'Turnos Más Demandados'},
        {'id': 'promedio_participantes', 'nombre': 'Promedio de Participantes'},
        {'id': 'reservas_por_carrera', 'nombre': 'Reservas por Carrera'},
        {'id': 'ocupacion_edificio', 'nombre': 'Ocupación por Edificio'},
        {'id': 'reservas_por_tipo', 'nombre': 'Reservas por Tipo de Usuario'},
        {'id': 'sanciones_por_tipo', 'nombre': 'Sanciones por Tipo'},
        {'id': 'efectividad', 'nombre': 'Efectividad de Reservas'},
        {'id': 'horas_semana', 'nombre': 'Horas Reservadas por Semana'},
        {'id': 'participantes_sancionados', 'nombre': 'Participantes Más Sancionados'},
        {'id': 'edificios_cancelaciones', 'nombre': 'Edificios con Más Cancelaciones'},
    ]
    return jsonify(reportes_list)

if __name__ == '__main__':
    print("\n🔍 Consultas SQL cargadas:")
    for key in CONSULTAS_SQL.keys():
        print(f"   ✓ {key}")
    print(f"\n📊 Total: {len(CONSULTAS_SQL)} reportes disponibles\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)