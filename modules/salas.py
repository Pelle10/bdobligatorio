#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de gestión de salas
ABM completo (Alta, Baja, Modificación)
"""

from db.connection import ejecutar_query, conectar
from mysql.connector import Error


def obtener_salas():
    """Obtiene todas las salas con información del edificio"""
    return ejecutar_query("""
        SELECT s.nombre_sala, s.edificio, s.capacidad, s.tipo_sala, e.direccion
        FROM sala s
        JOIN edificio e ON s.edificio = e.nombre_edificio
        ORDER BY s.edificio, s.nombre_sala
    """, fetchall=True)


def obtener_sala(nombre_sala, edificio):
    """Obtiene una sala específica"""
    return ejecutar_query("""
        SELECT s.nombre_sala, s.edificio, s.capacidad, s.tipo_sala, e.direccion
        FROM sala s
        JOIN edificio e ON s.edificio = e.nombre_edificio
        WHERE s.nombre_sala = %s AND s.edificio = %s
    """, (nombre_sala, edificio), fetchone=True)


def obtener_edificios():
    """Obtiene todos los edificios"""
    return ejecutar_query(
        "SELECT nombre_edificio, direccion FROM edificio ORDER BY nombre_edificio",
        fetchall=True
    )


def crear_sala(nombre_sala, edificio, capacidad, tipo_sala):
    """Crea una nueva sala"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Verificar que el edificio existe
        cursor.execute("SELECT nombre_edificio FROM edificio WHERE nombre_edificio = %s", (edificio,))
        if not cursor.fetchone():
            return False, "El edificio no existe"
        
        # Insertar sala
        cursor.execute("""
            INSERT INTO sala (nombre_sala, edificio, capacidad, tipo_sala)
            VALUES (%s, %s, %s, %s)
        """, (nombre_sala, edificio, capacidad, tipo_sala))
        
        conn.commit()
        return True, "Sala creada exitosamente"
        
    except Error as e:
        conn.rollback()
        if 'Duplicate entry' in str(e):
            return False, "Ya existe una sala con ese nombre en este edificio"
        return False, f"Error al crear sala: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def actualizar_sala(nombre_sala_original, edificio_original, nombre_sala_nuevo, 
                   edificio_nuevo, capacidad, tipo_sala):
    """Actualiza los datos de una sala"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Verificar edificio
        cursor.execute("SELECT nombre_edificio FROM edificio WHERE nombre_edificio = %s", (edificio_nuevo,))
        if not cursor.fetchone():
            return False, "El edificio no existe"
        
        # Actualizar sala
        cursor.execute("""
            UPDATE sala
            SET nombre_sala = %s, edificio = %s, capacidad = %s, tipo_sala = %s
            WHERE nombre_sala = %s AND edificio = %s
        """, (nombre_sala_nuevo, edificio_nuevo, capacidad, tipo_sala,
            nombre_sala_original, edificio_original))

        conn.commit()
        
        if cursor.rowcount > 0:
            return True, "Sala actualizada exitosamente"
        return False, "No se encontró la sala"
        
    except Error as e:
        conn.rollback()
        if 'Duplicate entry' in str(e):
            return False, "Ya existe una sala con ese nombre en este edificio"
        return False, f"Error al actualizar: {str(e)}"
    finally:
        cursor.close()
        conn.close()




def eliminar_sala(nombre_sala, edificio):
    """Elimina una sala"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        
        # Verificar si tiene reservas activas
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM reserva
            WHERE nombre_sala = %s AND edificio = %s AND estado = 'activa'
        """, (nombre_sala, edificio))
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            return False, "No se puede eliminar: tiene reservas activas"
        
        # Verificar si tiene reservas futuras
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM reserva
            WHERE nombre_sala = %s AND edificio = %s AND fecha >= CURDATE()
        """, (nombre_sala, edificio))
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            return False, "No se puede eliminar: tiene reservas futuras"
        
        # Eliminar sala
        cursor.execute("""
            DELETE FROM sala
            WHERE nombre_sala = %s AND edificio = %s
        """, (nombre_sala, edificio))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return True, "Sala eliminada exitosamente"
        return False, "No se encontró la sala"
        
    except Error as e:
        conn.rollback()
        return False, f"Error al eliminar: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def crear_edificio(nombre_edificio, direccion):
    """Crea un nuevo edificio"""
    conn = conectar()
    if not conn:
        return False, "Error de conexión"
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO edificio (nombre_edificio, direccion)
            VALUES (%s, %s)
        """, (nombre_edificio, direccion))
        
        conn.commit()
        return True, "Edificio creado exitosamente"
        
    except Error as e:
        conn.rollback()
        if 'Duplicate entry' in str(e):
            return False, "Ya existe un edificio con ese nombre"
        return False, f"Error al crear edificio: {str(e)}"
    finally:
        cursor.close()
        conn.close()


def obtener_tipos_sala():
    """Retorna los tipos de sala válidos"""
    return ['libre', 'posgrado', 'docente']


def obtener_estadisticas_sala(nombre_sala, edificio):
    """Obtiene estadísticas de uso de una sala"""
    stats = {}
    
    # Total de reservas
    result = ejecutar_query("""
        SELECT COUNT(*) as total
        FROM reserva
        WHERE nombre_sala = %s AND edificio = %s
    """, (nombre_sala, edificio), fetchone=True)
    stats['total_reservas'] = result['total'] if result else 0
    
    # Reservas activas
    result = ejecutar_query("""
        SELECT COUNT(*) as total
        FROM reserva
        WHERE nombre_sala = %s AND edificio = %s AND estado = 'activa'
    """, (nombre_sala, edificio), fetchone=True)
    stats['reservas_activas'] = result['total'] if result else 0
    
    # Tasa de cancelación
    result = ejecutar_query("""
        SELECT 
            COUNT(CASE WHEN estado = 'cancelada' THEN 1 END) as canceladas,
            COUNT(*) as total
        FROM reserva
        WHERE nombre_sala = %s AND edificio = %s
    """, (nombre_sala, edificio), fetchone=True)
    
    if result and result['total'] > 0:
        stats['tasa_cancelacion'] = round((result['canceladas'] / result['total']) * 100, 2)
    else:
        stats['tasa_cancelacion'] = 0
    
    return stats


# ============= FUNCIONES CLI (mantener compatibilidad) =============

def listar_salas():
    """Muestra todas las salas (CLI)"""
    salas = obtener_salas()
    
    if not salas:
        print("\n📋 No hay salas registradas.")
        return
    
    print("\n" + "="*100)
    print("🏢 LISTA DE SALAS")
    print("="*100)
    print(f"{'Sala':<15} {'Edificio':<20} {'Dirección':<30} {'Capacidad':<10} {'Tipo':<15}")
    print("-"*100)
    
    for s in salas:
        print(f"{s['nombre_sala']:<15} {s['edificio']:<20} {s['direccion']:<30} {s['capacidad']:<10} {s['tipo_sala']:<15}")
    print("="*100)