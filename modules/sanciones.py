#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de gestión de sanciones
ABM completo (Alta, Baja, Modificación)
"""

from db.connection import ejecutar_query, conectar
from mysql.connector import Error
from datetime import datetime, timedelta


def obtener_sanciones():
    """Obtiene todas las sanciones con información del participante"""
    return ejecutar_query("""
        SELECT s.id_sancion, s.ci_participante, p.nombre, p.apellido, p.email,
               s.fecha_inicio, s.fecha_fin,
               CASE
                   WHEN CURDATE() BETWEEN s.fecha_inicio AND s.fecha_fin THEN 'ACTIVA'
                   WHEN CURDATE() > s.fecha_fin THEN 'FINALIZADA'
                   ELSE 'FUTURA'
               END as estado,
               DATEDIFF(s.fecha_fin, s.fecha_inicio) as duracion_dias
        FROM sancion_participante s
        JOIN participante p ON s.ci_participante = p.ci
        ORDER BY s.fecha_inicio DESC
    """, fetchall=True)


def obtener_sancion(id_sancion):
    """Obtiene una sanción específica"""
    return ejecutar_query("""
        SELECT s.id_sancion, s.ci_participante, p.nombre, p.apellido, p.email,
               s.fecha_inicio, s.fecha_fin,
               CASE
                   WHEN CURDATE() BETWEEN s.fecha_inicio AND s.fecha_fin THEN 'ACTIVA'
                   WHEN CURDATE() > s.fecha_fin THEN 'FINALIZADA'
                   ELSE 'FUTURA'
               END as estado
        FROM sancion_participante s
        JOIN participante p ON s.ci_participante = p.ci
        WHERE s.id_sancion = %s
    """, (id_sancion,), fetchone=True)


def obtener_sanciones_participante(ci_participante):
    """Obtiene todas las sanciones de un participante"""
    return ejecutar_query("""
        SELECT id_sancion, fecha_inicio, fecha_fin,
               CASE
                   WHEN CURDATE() BETWEEN fecha_inicio AND fecha_fin THEN 'ACTIVA'
                   WHEN CURDATE() > fecha_fin THEN 'FINALIZADA'
                   ELSE 'FUTURA'
               END as estado
        FROM sancion_participante
        WHERE ci_participante = %s
        ORDER BY fecha_inicio DESC
    """, (ci_participante,), fetchall=True)


def tiene_sancion_activa(ci_participante):
    """Verifica si un participante tiene una sanción activa"""
    sancion = ejecutar_query("""
        SELECT id_sancion, fecha_fin
        FROM sancion_participante
        WHERE ci_participante = %s
        AND CURDATE() BETWEEN fecha_inicio AND fecha_fin
    """, (ci_participante,), fetchone=True)
    
    return sancion is not None, sancion


def crear_sancion(ci_participante, fecha_inicio, fecha_fin, motivo=None):
    """Crea una nueva sanción"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión", None
    
    try:
        cursor = conn.cursor()
        
        # Verificar que el participante existe
        cursor.execute("SELECT ci FROM participante WHERE ci = %s", (ci_participante,))
        if not cursor.fetchone():
            return False, "El participante no existe", None
        
        # Verificar que no tenga una sanción activa que se solape
        cursor.execute("""
            SELECT id_sancion
            FROM sancion_participante
            WHERE ci_participante = %s
            AND (
                (fecha_inicio <= %s AND fecha_fin >= %s) OR
                (fecha_inicio <= %s AND fecha_fin >= %s) OR
                (fecha_inicio >= %s AND fecha_fin <= %s)
            )
        """, (ci_participante, fecha_inicio, fecha_inicio, fecha_fin, fecha_fin, 
              fecha_inicio, fecha_fin))
        
        if cursor.fetchone():
            return False, "El participante ya tiene una sanción en ese período", None
        
        # Verificar que fecha_fin sea posterior a fecha_inicio
        if fecha_fin <= fecha_inicio:
            return False, "La fecha de fin debe ser posterior a la fecha de inicio", None
        
        # Insertar sanción
        cursor.execute("""
            INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s)
        """, (ci_participante, fecha_inicio, fecha_fin))
        
        id_sancion = cursor.lastrowid
        
        conn.commit()
        return True, "Sanción creada exitosamente", id_sancion
        
    except Error as e:
        conn.rollback()
        return False, f"Error al crear sanción: {str(e)}", None
    finally:
        cursor.close()
        conn.close()


def actualizar_sancion(id_sancion, fecha_inicio, fecha_fin):
    """Actualiza las fechas de una sanción"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Obtener CI del participante
        cursor.execute(
            "SELECT ci_participante FROM sancion_participante WHERE id_sancion = %s",
            (id_sancion,)
        )
        result = cursor.fetchone()
        
        if not result:
            return False, "Sanción no encontrada"
        
        ci_participante = result[0]
        
        # Verificar que no se solape con otras sanciones del mismo participante
        cursor.execute("""
            SELECT id_sancion
            FROM sancion_participante
            WHERE ci_participante = %s
            AND id_sancion != %s
            AND (
                (fecha_inicio <= %s AND fecha_fin >= %s) OR
                (fecha_inicio <= %s AND fecha_fin >= %s) OR
                (fecha_inicio >= %s AND fecha_fin <= %s)
            )
        """, (ci_participante, id_sancion, fecha_inicio, fecha_inicio, 
              fecha_fin, fecha_fin, fecha_inicio, fecha_fin))
        
        if cursor.fetchone():
            return False, "Las nuevas fechas se solapan con otra sanción"
        
        # Verificar que fecha_fin sea posterior a fecha_inicio
        if fecha_fin <= fecha_inicio:
            return False, "La fecha de fin debe ser posterior a la fecha de inicio"
        
        # Actualizar sanción
        cursor.execute("""
            UPDATE sancion_participante
            SET fecha_inicio = %s, fecha_fin = %s
            WHERE id_sancion = %s
        """, (fecha_inicio, fecha_fin, id_sancion))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return True, "Sanción actualizada exitosamente"
        return False, "No se encontró la sanción"
        
    except Error as e:
        conn.rollback()
        return False, f"Error al actualizar: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def eliminar_sancion(id_sancion):
    """Elimina una sanción"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Eliminar sanción
        cursor.execute("DELETE FROM sancion_participante WHERE id_sancion = %s", (id_sancion,))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return True, "Sanción eliminada exitosamente"
        return False, "No se encontró la sanción"
        
    except Error as e:
        conn.rollback()
        return False, f"Error al eliminar: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def finalizar_sancion(id_sancion):
    """Finaliza una sanción estableciendo fecha_fin a hoy"""
    fecha_hoy = datetime.now().date()
    
    resultado = ejecutar_query("""
        UPDATE sancion_participante
        SET fecha_fin = %s
        WHERE id_sancion = %s AND fecha_fin > %s
    """, (fecha_hoy, id_sancion, fecha_hoy), commit=True)
    
    if resultado:
        return True, "Sanción finalizada exitosamente"
    return False, "No se pudo finalizar la sanción"


def crear_sancion_automatica(ci_participante, dias=7):
    """Crea una sanción automática (por ejemplo, por inasistencia)"""
    fecha_inicio = datetime.now().date()
    fecha_fin = fecha_inicio + timedelta(days=dias)
    
    return crear_sancion(ci_participante, fecha_inicio, fecha_fin, 
                        f"Sanción automática por {dias} días")


def obtener_estadisticas_sanciones():
    """Obtiene estadísticas generales de sanciones"""
    stats = {}
    
    # Sanciones activas
    result = ejecutar_query("""
        SELECT COUNT(*) as total
        FROM sancion_participante
        WHERE CURDATE() BETWEEN fecha_inicio AND fecha_fin
    """, fetchone=True)
    stats['activas'] = result['total'] if result else 0
    
    # Sanciones totales
    result = ejecutar_query(
        "SELECT COUNT(*) as total FROM sancion_participante",
        fetchone=True
    )
    stats['totales'] = result['total'] if result else 0
    
    # Participantes sancionados actualmente
    result = ejecutar_query("""
        SELECT COUNT(DISTINCT ci_participante) as total
        FROM sancion_participante
        WHERE CURDATE() BETWEEN fecha_inicio AND fecha_fin
    """, fetchone=True)
    stats['participantes_sancionados'] = result['total'] if result else 0
    
    # Duración promedio
    result = ejecutar_query("""
        SELECT AVG(DATEDIFF(fecha_fin, fecha_inicio)) as promedio
        FROM sancion_participante
    """, fetchone=True)
    stats['duracion_promedio_dias'] = round(float(result['promedio']), 1) if result and result['promedio'] else 0
    
    return stats