#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de reportes y consultas SQL
"""

from db.connection import ejecutar_query

def reporte_salas_mas_reservadas():
    """Reporte 1: Salas más reservadas"""
    query = """
        SELECT s.nombre_sala, s.edificio, COUNT(r.id_reserva) as total_reservas
        FROM sala s
        LEFT JOIN reserva r ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        GROUP BY s.nombre_sala, s.edificio
        ORDER BY total_reservas DESC
        LIMIT 10
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*70)
    print("📊 SALAS MÁS RESERVADAS")
    print("="*70)
    print(f"{'Sala':<20} {'Edificio':<25} {'Total Reservas':<15}")
    print("-"*70)
    
    for r in resultados:
        print(f"{r['nombre_sala']:<20} {r['edificio']:<25} {r['total_reservas']:<15}")
    print("="*70)

def reporte_turnos_mas_demandados():
    """Reporte 2: Turnos más demandados"""
    query = """
        SELECT t.id_turno, CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario,
               COUNT(r.id_reserva) as total_reservas
        FROM turno t
        LEFT JOIN reserva r ON t.id_turno = r.id_turno
        GROUP BY t.id_turno, t.hora_inicio, t.hora_fin
        ORDER BY total_reservas DESC
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*60)
    print("📊 TURNOS MÁS DEMANDADOS")
    print("="*60)
    print(f"{'ID':<5} {'Horario':<25} {'Total Reservas':<15}")
    print("-"*60)
    
    for r in resultados:
        print(f"{r['id_turno']:<5} {r['horario']:<25} {r['total_reservas']:<15}")
    print("="*60)

def reporte_promedio_participantes():
    """Reporte 3: Promedio de participantes por sala"""
    query = """
        SELECT s.nombre_sala, s.edificio,
               AVG(participantes.num_part) as promedio_participantes
        FROM sala s
        LEFT JOIN (
            SELECT r.nombre_sala, r.edificio, COUNT(rp.ci_participante) as num_part
            FROM reserva r
            LEFT JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
            GROUP BY r.id_reserva, r.nombre_sala, r.edificio
        ) participantes ON s.nombre_sala = participantes.nombre_sala
                          AND s.edificio = participantes.edificio
        GROUP BY s.nombre_sala, s.edificio
        ORDER BY promedio_participantes DESC
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*70)
    print("📊 PROMEDIO DE PARTICIPANTES POR SALA")
    print("="*70)
    print(f"{'Sala':<20} {'Edificio':<25} {'Promedio':<15}")
    print("-"*70)
    
    for r in resultados:
        promedio = r['promedio_participantes'] if r['promedio_participantes'] else 0
        print(f"{r['nombre_sala']:<20} {r['edificio']:<25} {promedio:<15.2f}")
    print("="*70)

def reporte_reservas_por_carrera():
    """Reporte 4: Cantidad de reservas por carrera y facultad"""
    query = """
        SELECT f.nombre as facultad, pa.nombre_programa,
               COUNT(DISTINCT r.id_reserva) as total_reservas
        FROM facultad f
        JOIN programa_academico pa ON f.id_facultad = pa.id_facultad
        LEFT JOIN participante_programa_academico ppa ON pa.nombre_programa = ppa.nombre_programa
        LEFT JOIN reserva_participante rp ON ppa.ci_participante = rp.ci_participante
        LEFT JOIN reserva r ON rp.id_reserva = r.id_reserva
        GROUP BY f.nombre, pa.nombre_programa
        ORDER BY f.nombre, total_reservas DESC
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*80)
    print("📊 RESERVAS POR CARRERA Y FACULTAD")
    print("="*80)
    print(f"{'Facultad':<35} {'Programa':<30} {'Reservas':<10}")
    print("-"*80)
    
    for r in resultados:
        print(f"{r['facultad']:<35} {r['nombre_programa']:<30} {r['total_reservas']:<10}")
    print("="*80)

def reporte_ocupacion_por_edificio():
    """Reporte 5: Porcentaje de ocupación por edificio"""
    query = """
        SELECT e.nombre_edificio,
               COUNT(DISTINCT s.nombre_sala) as total_salas,
               COUNT(r.id_reserva) as total_reservas,
               ROUND(COUNT(r.id_reserva) * 100.0 / 
                     (COUNT(DISTINCT s.nombre_sala) * 
                      (SELECT COUNT(*) FROM turno) * 30), 2) as porcentaje_ocupacion
        FROM edificio e
        LEFT JOIN sala s ON e.nombre_edificio = s.edificio
        LEFT JOIN reserva r ON s.nombre_sala = r.nombre_sala 
                              AND s.edificio = r.edificio
                              AND r.fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY e.nombre_edificio
        ORDER BY porcentaje_ocupacion DESC
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*80)
    print("📊 PORCENTAJE DE OCUPACIÓN POR EDIFICIO (últimos 30 días)")
    print("="*80)
    print(f"{'Edificio':<25} {'Salas':<10} {'Reservas':<15} {'% Ocupación':<15}")
    print("-"*80)
    
    for r in resultados:
        print(f"{r['nombre_edificio']:<25} {r['total_salas']:<10} {r['total_reservas']:<15} {r['porcentaje_ocupacion']:<15}%")
    print("="*80)

def reporte_reservas_por_tipo_usuario():
    """Reporte 6: Reservas y asistencias por tipo de usuario"""
    query = """
        SELECT 
            CASE 
                WHEN ppa.rol = 'docente' THEN 'Docente'
                WHEN pa.tipo = 'posgrado' THEN 'Posgrado'
                ELSE 'Grado'
            END as tipo_usuario,
            COUNT(DISTINCT rp.id_reserva) as total_reservas,
            SUM(CASE WHEN rp.asistencia = TRUE THEN 1 ELSE 0 END) as total_asistencias
        FROM reserva_participante rp
        JOIN participante_programa_academico ppa ON rp.ci_participante = ppa.ci_participante
        JOIN programa_academico pa ON ppa.nombre_programa = pa.nombre_programa
        GROUP BY tipo_usuario
        ORDER BY total_reservas DESC
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*70)
    print("📊 RESERVAS Y ASISTENCIAS POR TIPO DE USUARIO")
    print("="*70)
    print(f"{'Tipo Usuario':<20} {'Total Reservas':<20} {'Asistencias':<20}")
    print("-"*70)
    
    for r in resultados:
        print(f"{r['tipo_usuario']:<20} {r['total_reservas']:<20} {r['total_asistencias']:<20}")
    print("="*70)

def reporte_sanciones_por_tipo():
    """Reporte 7: Cantidad de sanciones por tipo de usuario"""
    query = """
        SELECT 
            CASE 
                WHEN ppa.rol = 'docente' THEN 'Docente'
                WHEN pa.tipo = 'posgrado' THEN 'Posgrado'
                ELSE 'Grado'
            END as tipo_usuario,
            COUNT(DISTINCT sp.id_sancion) as total_sanciones
        FROM sancion_participante sp
        JOIN participante_programa_academico ppa ON sp.ci_participante = ppa.ci_participante
        JOIN programa_academico pa ON ppa.nombre_programa = pa.nombre_programa
        GROUP BY tipo_usuario
        ORDER BY total_sanciones DESC
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*60)
    print("📊 SANCIONES POR TIPO DE USUARIO")
    print("="*60)
    print(f"{'Tipo Usuario':<30} {'Total Sanciones':<20}")
    print("-"*60)
    
    for r in resultados:
        print(f"{r['tipo_usuario']:<30} {r['total_sanciones']:<20}")
    print("="*60)

def reporte_efectividad_reservas():
    """Reporte 8: Porcentaje de reservas utilizadas vs canceladas"""
    query = """
        SELECT 
            estado,
            COUNT(*) as total,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reserva), 2) as porcentaje
        FROM reserva
        GROUP BY estado
        ORDER BY total DESC
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*60)
    print("📊 EFECTIVIDAD DE RESERVAS")
    print("="*60)
    print(f"{'Estado':<20} {'Total':<15} {'Porcentaje':<15}")
    print("-"*60)
    
    for r in resultados:
        print(f"{r['estado']:<20} {r['total']:<15} {r['porcentaje']:<15}%")
    print("="*60)

def reporte_horas_por_semana():
    """Reporte 9: Total de horas reservadas por semana"""
    query = """
        SELECT 
            YEARWEEK(r.fecha, 1) as semana,
            DATE(DATE_SUB(r.fecha, INTERVAL WEEKDAY(r.fecha) DAY)) as inicio_semana,
            COUNT(*) as total_horas_reservadas
        FROM reserva r
        WHERE r.fecha >= DATE_SUB(CURDATE(), INTERVAL 8 WEEK)
        GROUP BY semana, inicio_semana
        ORDER BY semana DESC
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*60)
    print("📊 HORAS RESERVADAS POR SEMANA")
    print("="*60)
    print(f"{'Semana':<15} {'Inicio Semana':<20} {'Horas':<15}")
    print("-"*60)
    
    for r in resultados:
        print(f"{r['semana']:<15} {r['inicio_semana']:<20} {r['total_horas_reservadas']:<15}")
    print("="*60)

def reporte_participantes_mas_sancionados():
    """Reporte 10: Participantes con más sanciones"""
    query = """
        SELECT p.ci, p.nombre, p.apellido,
               COUNT(sp.id_sancion) as total_sanciones
        FROM participante p
        LEFT JOIN sancion_participante sp ON p.ci = sp.ci_participante
        GROUP BY p.ci, p.nombre, p.apellido
        HAVING total_sanciones > 0
        ORDER BY total_sanciones DESC
        LIMIT 10
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*80)
    print("📊 PARTICIPANTES CON MÁS SANCIONES")
    print("="*80)
    print(f"{'CI':<15} {'Nombre':<20} {'Apellido':<20} {'Sanciones':<15}")
    print("-"*80)
    
    for r in resultados:
        print(f"{r['ci']:<15} {r['nombre']:<20} {r['apellido']:<20} {r['total_sanciones']:<15}")
    print("="*80)

def reporte_edificios_mas_cancelaciones():
    """Reporte 11: Edificios con más reservas canceladas"""
    query = """
        SELECT e.nombre_edificio,
               COUNT(CASE WHEN r.estado = 'cancelada' THEN 1 END) as canceladas,
               COUNT(r.id_reserva) as total_reservas,
               ROUND(COUNT(CASE WHEN r.estado = 'cancelada' THEN 1 END) * 100.0 / 
                     NULLIF(COUNT(r.id_reserva), 0), 2) as porcentaje_cancelacion
        FROM edificio e
        LEFT JOIN sala s ON e.nombre_edificio = s.edificio
        LEFT JOIN reserva r ON s.nombre_sala = r.nombre_sala AND s.edificio = r.edificio
        GROUP BY e.nombre_edificio
        HAVING total_reservas > 0
        ORDER BY canceladas DESC
    """
    resultados = ejecutar_query(query, fetchall=True)
    
    print("\n" + "="*80)
    print("📊 EDIFICIOS CON MÁS CANCELACIONES")
    print("="*80)
    print(f"{'Edificio':<25} {'Canceladas':<15} {'Total':<15} {'% Cancel.':<15}")
    print("-"*80)
    
    for r in resultados:
        print(f"{r['nombre_edificio']:<25} {r['canceladas']:<15} {r['total_reservas']:<15} {r['porcentaje_cancelacion']:<15}%")
    print("="*80)

def menu_reportes():
    """Menú de reportes"""
    while True:
        print("\n" + "="*50)
        print("📊 REPORTES")
        print("="*50)
        print("1. Salas más reservadas")
        print("2. Turnos más demandados")
        print("3. Promedio de participantes por sala")
        print("4. Reservas por carrera y facultad")
        print("5. Porcentaje de ocupación por edificio")
        print("6. Reservas y asistencias por tipo de usuario")
        print("7. Sanciones por tipo de usuario")
        print("8. Efectividad de reservas")
        print("9. Horas reservadas por semana")
        print("10. Participantes con más sanciones")
        print("11. Edificios con más cancelaciones")
        print("0. Volver al menú principal")
        print("-"*50)
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            reporte_salas_mas_reservadas()
        elif opcion == '2':
            reporte_turnos_mas_demandados()
        elif opcion == '3':
            reporte_promedio_participantes()
        elif opcion == '4':
            reporte_reservas_por_carrera()
        elif opcion == '5':
            reporte_ocupacion_por_edificio()
        elif opcion == '6':
            reporte_reservas_por_tipo_usuario()
        elif opcion == '7':
            reporte_sanciones_por_tipo()
        elif opcion == '8':
            reporte_efectividad_reservas()
        elif opcion == '9':
            reporte_horas_por_semana()
        elif opcion == '10':
            reporte_participantes_mas_sancionados()
        elif opcion == '11':
            reporte_edificios_mas_cancelaciones()
        elif opcion == '0':
            break
        else:
            print("❌ Opción inválida.")