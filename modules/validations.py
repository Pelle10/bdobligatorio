#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de validaciones de reglas de negocio
"""

from datetime import timedelta
from db.connection import ejecutar_query

def validar_sancion(ci_participante):
    """Verifica si un participante tiene sanción activa"""
    query = """
        SELECT * FROM sancion_participante
        WHERE ci_participante = %s
        AND CURDATE() BETWEEN fecha_inicio AND fecha_fin
    """
    sancion = ejecutar_query(query, (ci_participante,), fetchone=True)
    
    if sancion:
        print(f"❌ El participante tiene sanción activa hasta {sancion['fecha_fin']}")
        return False
    return True

def validar_limite_horas_dia(ci_participante, fecha, id_turno):
    """Verifica límite de 2 horas por día"""
    query = """
        SELECT COUNT(*) as total
        FROM reserva_participante rp
        JOIN reserva r ON rp.id_reserva = r.id_reserva
        WHERE rp.ci_participante = %s
        AND r.fecha = %s
        AND r.estado = 'activa'
    """
    resultado = ejecutar_query(query, (ci_participante, fecha), fetchone=True)
    
    if resultado and resultado['total'] >= 2:
        print("❌ El participante ya tiene 2 horas reservadas para este día (límite alcanzado)")
        return False
    return True

def validar_limite_reservas_semana(ci_participante, fecha):
    """Verifica límite de 3 reservas activas por semana"""
    fecha_inicio_semana = fecha - timedelta(days=fecha.weekday())
    fecha_fin_semana = fecha_inicio_semana + timedelta(days=6)
    
    query = """
        SELECT COUNT(DISTINCT r.id_reserva) as total
        FROM reserva_participante rp
        JOIN reserva r ON rp.id_reserva = r.id_reserva
        WHERE rp.ci_participante = %s
        AND r.fecha BETWEEN %s AND %s
        AND r.estado = 'activa'
    """
    resultado = ejecutar_query(query, (ci_participante, fecha_inicio_semana, fecha_fin_semana), fetchone=True)
    
    if resultado and resultado['total'] >= 3:
        print("❌ El participante ya tiene 3 reservas activas esta semana (límite alcanzado)")
        return False
    return True

def validar_capacidad_sala(nombre_sala, edificio, id_reserva, num_participantes):
    """Verifica que no se exceda la capacidad de la sala"""
    # Obtener capacidad de la sala
    sala = ejecutar_query(
        "SELECT capacidad FROM sala WHERE nombre_sala = %s AND edificio = %s",
        (nombre_sala, edificio),
        fetchone=True
    )
    
    if not sala:
        print("❌ Sala no encontrada.")
        return False
    
    # Contar participantes actuales en la reserva
    query = """
        SELECT COUNT(*) as total
        FROM reserva_participante
        WHERE id_reserva = %s
    """
    resultado = ejecutar_query(query, (id_reserva,), fetchone=True)
    total_actual = resultado['total'] if resultado else 0
    
    if total_actual + num_participantes > sala['capacidad']:
        print(f"❌ La capacidad de la sala ({sala['capacidad']}) sería excedida.")
        return False
    return True

def es_usuario_privilegiado(ci_participante):
    """Verifica si es docente o estudiante de posgrado"""
    query = """
        SELECT ppa.rol, pa.tipo
        FROM participante_programa_academico ppa
        JOIN programa_academico pa ON ppa.nombre_programa = pa.nombre_programa
        WHERE ppa.ci_participante = %s
    """
    resultado = ejecutar_query(query, (ci_participante,), fetchone=True)
    
    if resultado:
        return resultado['rol'] == 'docente' or resultado['tipo'] == 'posgrado'
    return False

def sala_compatible_usuario(nombre_sala, edificio, ci_participante):
    """Verifica si el usuario puede usar el tipo de sala"""
    # Obtener tipo de sala
    sala = ejecutar_query(
        "SELECT tipo_sala FROM sala WHERE nombre_sala = %s AND edificio = %s",
        (nombre_sala, edificio),
        fetchone=True
    )
    
    if not sala:
        return False
    
    tipo_sala = sala['tipo_sala']
    
    # Salas libres: todos pueden usarlas
    if tipo_sala == 'libre':
        return True
    
    # Salas posgrado y docente: solo usuarios privilegiados
    if tipo_sala in ['posgrado', 'docente']:
        return es_usuario_privilegiado(ci_participante)
    
    return False