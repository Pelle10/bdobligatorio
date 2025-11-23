#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de gestión de reservas
"""

from datetime import datetime, timedelta, date
from db.connection import ejecutar_query, conectar
from mysql.connector import Error
from modules.validations import (
    validar_sancion, validar_limite_horas_dia, validar_limite_reservas_semana,
    validar_capacidad_sala, es_usuario_privilegiado, sala_compatible_usuario
)
from modules.salas import listar_salas

def listar_reservas():
    """Muestra todas las reservas"""
    query = """
        SELECT r.id_reserva, r.nombre_sala, r.edificio, r.fecha,
               CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario,
               r.estado,
               COUNT(rp.ci_participante) as num_participantes
        FROM reserva r
        JOIN turno t ON r.id_turno = t.id_turno
        LEFT JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
        GROUP BY r.id_reserva
        ORDER BY r.fecha DESC, t.hora_inicio
        LIMIT 50
    """
    reservas = ejecutar_query(query, fetchall=True)
    
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

def crear_reserva():
    """Crea una nueva reserva"""
    print("\n➕ CREAR RESERVA")
    print("-" * 50)
    
    # Listar salas
    listar_salas()
    
    nombre_sala = input("\nNombre de la sala: ").strip()
    edificio = input("Edificio: ").strip()
    
    # Verificar que la sala existe
    sala = ejecutar_query(
        "SELECT * FROM sala WHERE nombre_sala = %s AND edificio = %s",
        (nombre_sala, edificio),
        fetchone=True
    )
    
    if not sala:
        print("❌ Sala no encontrada.")
        return
    
    # Seleccionar fecha
    fecha_str = input("Fecha (YYYY-MM-DD) [hoy]: ").strip()
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            print("❌ Formato de fecha inválido.")
            return
    else:
        fecha = date.today()
    
    # Listar turnos disponibles
    print("\nTurnos disponibles:")
    turnos = ejecutar_query("SELECT * FROM turno ORDER BY hora_inicio", fetchall=True)
    for t in turnos:
        print(f"  {t['id_turno']}: {t['hora_inicio']} - {t['hora_fin']}")
    
    id_turno = input("\nID del turno: ").strip()
    
    try:
        id_turno = int(id_turno)
    except ValueError:
        print("❌ ID de turno inválido.")
        return
    
    # Verificar que el turno no esté ocupado
    reserva_existente = ejecutar_query(
        """SELECT * FROM reserva
           WHERE nombre_sala = %s AND edificio = %s
           AND fecha = %s AND id_turno = %s""",
        (nombre_sala, edificio, fecha, id_turno),
        fetchone=True
    )
    
    if reserva_existente:
        print("❌ Ya existe una reserva para esta sala, fecha y turno.")
        return
    
    # Solicitar participantes
    print("\nIngrese las CI de los participantes (separadas por comas):")
    cis = input("CI: ").strip().split(',')
    cis = [ci.strip() for ci in cis]
    
    if not cis:
        print("❌ Debe ingresar al menos un participante.")
        return
    
    # Validar participantes
    participantes_validos = []
    for ci in cis:
        participante = ejecutar_query(
            "SELECT * FROM participante WHERE ci = %s",
            (ci,),
            fetchone=True
        )
        
        if not participante:
            print(f"❌ Participante con CI {ci} no encontrado.")
            return
        
        participantes_validos.append(ci)
    
    # Validaciones de reglas de negocio
    for ci in participantes_validos:
        # Verificar sanción
        if not validar_sancion(ci):
            return
        
        # Verificar compatibilidad de sala
        if not sala_compatible_usuario(nombre_sala, edificio, ci):
            print(f"❌ El participante {ci} no puede reservar salas de tipo '{sala['tipo_sala']}'")
            return
        
        # Si no es usuario privilegiado, aplicar restricciones
        if not es_usuario_privilegiado(ci):
            if not validar_limite_horas_dia(ci, fecha, id_turno):
                return
            if not validar_limite_reservas_semana(ci, fecha):
                return
    
    # Crear reserva
    conn = conectar()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Insertar reserva
        cursor.execute(
            """INSERT INTO reserva (nombre_sala, edificio, fecha, id_turno, estado)
               VALUES (%s, %s, %s, %s, 'activa')""",
            (nombre_sala, edificio, fecha, id_turno)
        )
        
        id_reserva = cursor.lastrowid
        
        # Verificar capacidad
        if not validar_capacidad_sala(nombre_sala, edificio, id_reserva, len(participantes_validos)):
            conn.rollback()
            return
        
        # Insertar participantes
        for ci in participantes_validos:
            cursor.execute(
                """INSERT INTO reserva_participante (ci_participante, id_reserva)
                   VALUES (%s, %s)""",
                (ci, id_reserva)
            )
        
        conn.commit()
        print(f"✅ Reserva #{id_reserva} creada exitosamente.")
        
    except Error as e:
        conn.rollback()
        print(f"❌ Error al crear reserva: {e}")
    finally:
        cursor.close()
        conn.close()

def cancelar_reserva():
    """Cancela una reserva"""
    listar_reservas()
    
    id_reserva = input("\nID de la reserva a cancelar: ").strip()
    
    try:
        id_reserva = int(id_reserva)
    except ValueError:
        print("❌ ID de reserva inválido.")
        return
    
    confirmacion = input(f"⚠️  ¿Confirma cancelar la reserva #{id_reserva}? (s/n): ")
    if confirmacion.lower() != 's':
        print("❌ Operación cancelada.")
        return
    
    resultado = ejecutar_query(
        "UPDATE reserva SET estado = 'cancelada' WHERE id_reserva = %s",
        (id_reserva,),
        commit=True
    )
    
    if resultado:
        print("✅ Reserva cancelada exitosamente.")
    else:
        print("❌ Error al cancelar reserva.")

def registrar_asistencia():
    """Registra asistencia a una reserva"""
    listar_reservas()
    
    id_reserva = input("\nID de la reserva: ").strip()
    
    try:
        id_reserva = int(id_reserva)
    except ValueError:
        print("❌ ID de reserva inválido.")
        return
    
    # Listar participantes de la reserva
    query = """
        SELECT rp.ci_participante, p.nombre, p.apellido, rp.asistencia
        FROM reserva_participante rp
        JOIN participante p ON rp.ci_participante = p.ci
        WHERE rp.id_reserva = %s
    """
    participantes = ejecutar_query(query, (id_reserva,), fetchall=True)
    
    if not participantes:
        print("❌ Reserva no encontrada o sin participantes.")
        return
    
    print("\nParticipantes:")
    for p in participantes:
        asist = "✓" if p['asistencia'] else "✗" if p['asistencia'] is False else "?"
        print(f"  {p['ci_participante']}: {p['nombre']} {p['apellido']} - Asistencia: {asist}")
    
    ci = input("\nCI del participante: ").strip()
    asistio = input("¿Asistió? (s/n): ").strip().lower()
    
    if asistio not in ['s', 'n']:
        print("❌ Respuesta inválida.")
        return
    
    asistencia = True if asistio == 's' else False
    
    conn = conectar()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Actualizar asistencia
        cursor.execute(
            """UPDATE reserva_participante
               SET asistencia = %s
               WHERE id_reserva = %s AND ci_participante = %s""",
            (asistencia, id_reserva, ci)
        )
        
        conn.commit()
        
        # Verificar si ningún participante asistió
        cursor.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN asistencia = TRUE THEN 1 ELSE 0 END) as asistieron
               FROM reserva_participante
               WHERE id_reserva = %s""",
            (id_reserva,)
        )
        
        resultado = cursor.fetchone()
        
        if resultado[0] > 0 and resultado[1] == 0:
            # Nadie asistió, aplicar sanciones
            print("⚠️  Ningún participante asistió. Aplicando sanciones...")
            
            fecha_inicio = date.today()
            fecha_fin = fecha_inicio + timedelta(days=60)  # 2 meses
            
            cursor.execute(
                """SELECT ci_participante FROM reserva_participante
                   WHERE id_reserva = %s""",
                (id_reserva,)
            )
            
            for (ci_part,) in cursor.fetchall():
                cursor.execute(
                    """INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin)
                       VALUES (%s, %s, %s)""",
                    (ci_part, fecha_inicio, fecha_fin)
                )
            
            # Cambiar estado de reserva
            cursor.execute(
                "UPDATE reserva SET estado = 'sin asistencia' WHERE id_reserva = %s",
                (id_reserva,)
            )
            
            conn.commit()
            print("✅ Sanciones aplicadas (2 meses).")
        
        print("✅ Asistencia registrada exitosamente.")
        
    except Error as e:
        conn.rollback()
        print(f"❌ Error al registrar asistencia: {e}")
    finally:
        cursor.close()
        conn.close()

def menu_reservas():
    """Menú de gestión de reservas"""
    while True:
        print("\n" + "="*50)
        print("📅 GESTIÓN DE RESERVAS")
        print("="*50)
        print("1. Listar reservas")
        print("2. Crear reserva")
        print("3. Cancelar reserva")
        print("4. Registrar asistencia")
        print("0. Volver al menú principal")
        print("-"*50)
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            listar_reservas()
        elif opcion == '2':
            crear_reserva()
        elif opcion == '3':
            cancelar_reserva()
        elif opcion == '4':
            registrar_asistencia()
        elif opcion == '0':
            break
        else:
            print("❌ Opción inválida.")