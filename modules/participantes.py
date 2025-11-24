#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de gestión de participantes
ABM completo (Alta, Baja, Modificación)
"""

from db.connection import ejecutar_query, conectar
from mysql.connector import Error
import bcrypt


def obtener_participantes():
    """Obtiene todos los participantes con sus programas"""
    return ejecutar_query("""
        SELECT p.ci, p.nombre, p.apellido, p.email,
               GROUP_CONCAT(CONCAT(ppa.rol, ' en ', ppa.nombre_programa) SEPARATOR ', ') as programas
        FROM participante p
        LEFT JOIN participante_programa_academico ppa ON p.ci = ppa.ci_participante
        GROUP BY p.ci ORDER BY p.apellido, p.nombre
    """, fetchall=True)


def obtener_participante(ci):
    """Obtiene un participante específico"""
    participante = ejecutar_query(
        "SELECT * FROM participante WHERE ci = %s",
        (ci,),
        fetchone=True
    )
    
    if participante:
        # Obtener programas del participante
        programas = ejecutar_query("""
            SELECT nombre_programa, rol
            FROM participante_programa_academico
            WHERE ci_participante = %s
        """, (ci,), fetchall=True)
        participante['programas'] = programas
    
    return participante


def crear_participante(ci, nombre, apellido, email, password, programa, rol):
    """Crea un nuevo participante"""
    hash_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = conectar()
    if not conn:
        return False, "Error de conexión con la base de datos"
    
    try:
        cursor = conn.cursor()
        
        # Insertar login
        cursor.execute(
            "INSERT INTO login (correo, contrasena) VALUES (%s, %s)",
            (email, hash_pass)
        )
        
        # Insertar participante
        cursor.execute(
            "INSERT INTO participante (ci, nombre, apellido, email) VALUES (%s, %s, %s, %s)",
            (ci, nombre, apellido, email)
        )
        
        # Insertar programa académico
        cursor.execute("""
            INSERT INTO participante_programa_academico (ci_participante, nombre_programa, rol)
            VALUES (%s, %s, %s)
        """, (ci, programa, rol))
        
        conn.commit()
        return True, "Participante creado exitosamente"
        
    except Error as e:
        conn.rollback()
        if 'Duplicate entry' in str(e):
            return False, "El email o CI ya están registrados"
        return False, f"Error al crear participante: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def actualizar_participante(ci, nombre, apellido, email):
    """Actualiza los datos de un participante"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()

        # 1) Obtener email actual ANTES de actualizar
        cursor.execute("SELECT email FROM participante WHERE ci = %s", (ci,))
        row = cursor.fetchone()

        if not row:
            return False, "No se encontró el participante"

        email_viejo = row[0]

        # 2) Actualizar login primero (ANTES de cambiar participante)
        cursor.execute("""
            UPDATE login
            SET correo = %s
            WHERE correo = %s
        """, (email, email_viejo))

        # 3) Actualizar participante
        cursor.execute("""
            UPDATE participante
            SET nombre = %s, apellido = %s, email = %s
            WHERE ci = %s
        """, (nombre, apellido, email, ci))

        conn.commit()
        return True, "Participante actualizado exitosamente"
        
    except Error as e:
        conn.rollback()
        if 'Duplicate entry' in str(e):
            return False, "El email ya está registrado"
        return False, f"Error al actualizar: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def actualizar_password(email, nueva_password):
    """Actualiza la contraseña de un participante"""
    hash_pass = bcrypt.hashpw(nueva_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    resultado = ejecutar_query(
        "UPDATE login SET contrasena = %s WHERE correo = %s",
        (hash_pass, email),
        commit=True
    )
    
    return resultado


def eliminar_participante(ci):
    """Elimina un participante y todos sus registros relacionados"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Verificar si tiene reservas activas
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM reserva_participante rp
            JOIN reserva r ON rp.id_reserva = r.id_reserva
            WHERE rp.ci_participante = %s AND r.estado = 'activa'
        """, (ci,))
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            return False, "No se puede eliminar: tiene reservas activas"
        
        # Obtener email para eliminar login
        cursor.execute("SELECT email FROM participante WHERE ci = %s", (ci,))
        result = cursor.fetchone()
        email = result[0] if result else None
        
        # Eliminar en orden (por foreign keys)
        # 1. Sanciones
        cursor.execute("DELETE FROM sancion_participante WHERE ci_participante = %s", (ci,))
        
        # 2. Reservas participante
        cursor.execute("DELETE FROM reserva_participante WHERE ci_participante = %s", (ci,))
        
        # 3. Programas académicos
        cursor.execute("DELETE FROM participante_programa_academico WHERE ci_participante = %s", (ci,))
        
        # 4. Participante
        cursor.execute("DELETE FROM participante WHERE ci = %s", (ci,))
        
        # 5. Login
        if email:
            cursor.execute("DELETE FROM login WHERE correo = %s", (email,))
        
        conn.commit()
        return True, "Participante eliminado exitosamente"
        
    except Error as e:
        conn.rollback()
        return False, f"Error al eliminar: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def agregar_programa_participante(ci, nombre_programa, rol):
    """Agrega un programa académico a un participante"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO participante_programa_academico (ci_participante, nombre_programa, rol)
            VALUES (%s, %s, %s)
        """, (ci, nombre_programa, rol))
        
        conn.commit()
        return True, "Programa agregado exitosamente"
        
    except Error as e:
        conn.rollback()
        if 'Duplicate entry' in str(e):
            return False, "El participante ya está inscrito en este programa"
        return False, f"Error al agregar programa: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def eliminar_programa_participante(ci, nombre_programa):
    """Elimina un programa académico de un participante"""
    resultado = ejecutar_query("""
        DELETE FROM participante_programa_academico
        WHERE ci_participante = %s AND nombre_programa = %s
    """, (ci, nombre_programa), commit=True)
    
    return resultado