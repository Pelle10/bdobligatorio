#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de gestión de reservas
ABM completo (Alta, Baja, Modificación)
"""

from db.connection import ejecutar_query, conectar
from mysql.connector import Error
from datetime import datetime


def obtener_reservas(limite=100):
    """Obtiene todas las reservas con información detallada"""
    return ejecutar_query("""
        SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha,
               CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario,
               t.hora_inicio, t.hora_fin, r.id_turno, r.estado,
               COUNT(rp.ci_participante) as num_participantes
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        LEFT JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
        GROUP BY r.id_reserva
        ORDER BY r.fecha DESC, t.hora_inicio DESC
        LIMIT %s
    """, (limite,), fetchall=True)


def obtener_reserva(id_reserva):
    """Obtiene una reserva específica con participantes"""
    reserva = ejecutar_query("""
        SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha, r.id_turno, r.estado,
               CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario,
               t.hora_inicio, t.hora_fin,
               s.capacidad, s.tipo_sala
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        JOIN sala s ON r.nombre_sala = s.nombre_sala AND r.edificio = s.edificio
        WHERE r.id_reserva = %s
    """, (id_reserva,), fetchone=True)
    
    if reserva:
        # Obtener participantes
        participantes = ejecutar_query("""
            SELECT rp.ci_participante, p.nombre, p.apellido, p.email, rp.asistencia
            FROM reserva_participante rp
            JOIN participante p ON rp.ci_participante = p.ci
            WHERE rp.id_reserva = %s
        """, (id_reserva,), fetchall=True)
        reserva['participantes'] = participantes
    
    return reserva


def obtener_reservas_participante(ci_participante, limite=20):
    """Obtiene las reservas de un participante específico"""
    return ejecutar_query("""
        SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha, r.estado,
               CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario,
               rp.asistencia
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
        WHERE rp.ci_participante = %s
        ORDER BY r.fecha DESC, t.hora_inicio DESC
        LIMIT %s
    """, (ci_participante, limite), fetchall=True)


def crear_reserva(nombre_sala, edificio, fecha, id_turno, ci_creador):
    """Crea una nueva reserva"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión", None
    
    try:
        cursor = conn.cursor()
        
        # Verificar que no exista una reserva en ese turno
        cursor.execute("""
            SELECT id_reserva FROM reserva
            WHERE nombre_sala = %s AND edificio = %s
            AND fecha = %s AND id_turno = %s
        """, (nombre_sala, edificio, fecha, id_turno))
        
        if cursor.fetchone():
            return False, "Este turno ya está reservado", None
        
        # Insertar reserva
        cursor.execute("""
            INSERT INTO reserva (nombre_sala, edificio, fecha, id_turno, estado)
            VALUES (%s, %s, %s, %s, 'activa')
        """, (nombre_sala, edificio, fecha, id_turno))
        
        id_reserva = cursor.lastrowid
        
        # Agregar al creador como participante
        cursor.execute("""
            INSERT INTO reserva_participante (ci_participante, id_reserva)
            VALUES (%s, %s)
        """, (ci_creador, id_reserva))
        
        conn.commit()
        return True, "Reserva creada exitosamente", id_reserva
        
    except Error as e:
        conn.rollback()
        return False, f"Error al crear reserva: {str(e)}", None
    finally:
        cursor.close()
        conn.close()


def actualizar_reserva(id_reserva, nombre_sala, edificio, fecha, id_turno):
    """Actualiza una reserva existente"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Verificar que la nueva combinación no exista (excepto la actual)
        cursor.execute("""
            SELECT id_reserva FROM reserva
            WHERE nombre_sala = %s AND edificio = %s
            AND fecha = %s AND id_turno = %s
            AND id_reserva != %s
        """, (nombre_sala, edificio, fecha, id_turno, id_reserva))
        
        if cursor.fetchone():
            return False, "Ya existe una reserva en ese turno"
        
        # Actualizar reserva
        cursor.execute("""
            UPDATE reserva
            SET nombre_sala = %s, edificio = %s, fecha = %s, id_turno = %s
            WHERE id_reserva = %s
        """, (nombre_sala, edificio, fecha, id_turno, id_reserva))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return True, "Reserva actualizada exitosamente"
        return False, "No se encontró la reserva"
        
    except Error as e:
        conn.rollback()
        return False, f"Error al actualizar: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def cambiar_estado_reserva(id_reserva, nuevo_estado):
    """Cambia el estado de una reserva"""
    estados_validos = ['activa', 'cancelada', 'finalizada', 'sin asistencia']
    
    if nuevo_estado not in estados_validos:
        return False, "Estado no válido"
    
    resultado = ejecutar_query(
        "UPDATE reserva SET estado = %s WHERE id_reserva = %s",
        (nuevo_estado, id_reserva),
        commit=True
    )
    
    if resultado:
        return True, f"Estado cambiado a '{nuevo_estado}'"
    return False, "No se pudo cambiar el estado"


def cancelar_reserva(id_reserva):
    """Cancela una reserva"""
    return cambiar_estado_reserva(id_reserva, 'cancelada')


def eliminar_reserva(id_reserva):
    """Elimina físicamente una reserva (solo si está cancelada)"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Verificar estado
        cursor.execute("SELECT estado FROM reserva WHERE id_reserva = %s", (id_reserva,))
        result = cursor.fetchone()
        
        if not result:
            return False, "Reserva no encontrada"
        
        if result[0] not in ['cancelada', 'sin asistencia']:
            return False, "Solo se pueden eliminar reservas canceladas o sin asistencia"
        
        # Eliminar participantes primero
        cursor.execute("DELETE FROM reserva_participante WHERE id_reserva = %s", (id_reserva,))
        
        # Eliminar reserva
        cursor.execute("DELETE FROM reserva WHERE id_reserva = %s", (id_reserva,))
        
        conn.commit()
        return True, "Reserva eliminada exitosamente"
        
    except Error as e:
        conn.rollback()
        return False, f"Error al eliminar: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def agregar_participante_reserva(id_reserva, ci_participante):
    """Agrega un participante a una reserva"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Verificar capacidad
        cursor.execute("""
            SELECT s.capacidad, COUNT(rp.ci_participante) as actual
            FROM reserva r
            JOIN sala s ON r.nombre_sala = s.nombre_sala AND r.edificio = s.edificio
            LEFT JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
            WHERE r.id_reserva = %s
            GROUP BY s.capacidad
        """, (id_reserva,))
        
        result = cursor.fetchone()
        if result and result[1] >= result[0]:
            return False, "La sala ha alcanzado su capacidad máxima"
        
        # Agregar participante
        cursor.execute("""
            INSERT INTO reserva_participante (ci_participante, id_reserva)
            VALUES (%s, %s)
        """, (ci_participante, id_reserva))
        
        conn.commit()
        return True, "Participante agregado exitosamente"
        
    except Error as e:
        conn.rollback()
        if 'Duplicate entry' in str(e):
            return False, "El participante ya está en esta reserva"
        return False, f"Error al agregar: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def eliminar_participante_reserva(id_reserva, ci_participante):
    """Elimina un participante de una reserva"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Verificar que no sea el único participante
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM reserva_participante
            WHERE id_reserva = %s
        """, (id_reserva,))
        
        result = cursor.fetchone()
        if result and result[0] <= 1:
            return False, "No se puede eliminar el único participante de la reserva"
        
        # Eliminar participante
        cursor.execute("""
            DELETE FROM reserva_participante
            WHERE id_reserva = %s AND ci_participante = %s
        """, (id_reserva, ci_participante))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return True, "Participante eliminado de la reserva"
        return False, "No se encontró el participante en esta reserva"
        
    except Error as e:
        conn.rollback()
        return False, f"Error al eliminar: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def marcar_asistencia(id_reserva, ci_participante, asistio):
    """Marca la asistencia de un participante"""
    resultado = ejecutar_query("""
        UPDATE reserva_participante
        SET asistencia = %s
        WHERE id_reserva = %s AND ci_participante = %s
    """, (asistio, id_reserva, ci_participante), commit=True)
    
    if resultado:
        return True, "Asistencia registrada"
    return False, "No se pudo registrar la asistencia"


def obtener_turnos():
    """Obtiene todos los turnos disponibles"""
    return ejecutar_query(
        "SELECT * FROM turno ORDER BY hora_inicio",
        fetchall=True
    )


# ============= FUNCIONES CLI (mantener compatibilidad) =============

def listar_reservas():
    """Muestra todas las reservas (CLI)"""
    reservas = obtener_reservas(50)
    
    if not reservas:
        print("\n📋 No hay reservas registradas.")
        return
    
    print("\n" + "="*110)
    print("📅 LISTA DE RESERVAS")
    print("="*110)
    print(f"{'ID':<5} {'Sala':<15} {'Edificio':<20} {'Fecha':<12} {'Horario':<18} {'Participantes':<14} {'Estado':<15}")
    print("-"*110)
    
    for r in reservas:
        print(f"{r['id_reserva']:<5} {r['nombre_sala']:<15} {r['edificio']:<20} {r['fecha']:<12} {r['horario']:<18} {r['num_participantes']:<14} {r['estado']:<15}")
    print("="*110)