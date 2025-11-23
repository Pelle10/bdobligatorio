#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de gestión de sanciones
"""

from datetime import date, timedelta
from db.connection import ejecutar_query
from modules.participantes import listar_participantes

def listar_sanciones():
    """Muestra todas las sanciones"""
    query = """
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
    """
    sanciones = ejecutar_query(query, fetchall=True)
    
    if not sanciones:
        print("\n📋 No hay sanciones registradas.")
        return
    
    print("\n" + "="*100)
    print("⚠️  LISTA DE SANCIONES")
    print("="*100)
    print(f"{'ID':<5} {'CI':<12} {'Nombre':<20} {'Apellido':<20} {'Desde':<12} {'Hasta':<12} {'Estado':<12}")
    print("-"*100)
    
    for s in sanciones:
        print(f"{s['id_sancion']:<5} {s['ci_participante']:<12} {s['nombre']:<20} {s['apellido']:<20} {s['fecha_inicio']:<12} {s['fecha_fin']:<12} {s['estado']:<12}")
    print("="*100)

def crear_sancion():
    """Crea una sanción manual"""
    print("\n➕ CREAR SANCIÓN")
    print("-" * 50)
    
    listar_participantes()
    
    ci = input("\nCI del participante: ").strip()
    dias = input("Duración en días: ").strip()
    
    try:
        dias = int(dias)
        if dias <= 0:
            raise ValueError
    except ValueError:
        print("❌ La duración debe ser un número positivo.")
        return
    
    fecha_inicio = date.today()
    fecha_fin = fecha_inicio + timedelta(days=dias)
    
    resultado = ejecutar_query(
        "INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin) VALUES (%s, %s, %s)",
        (ci, fecha_inicio, fecha_fin),
        commit=True
    )
    
    if resultado:
        print(f"✅ Sanción creada exitosamente hasta {fecha_fin}.")
    else:
        print("❌ Error al crear sanción.")

def eliminar_sancion():
    """Elimina una sanción"""
    listar_sanciones()
    
    id_sancion = input("\nID de la sanción a eliminar: ").strip()
    
    try:
        id_sancion = int(id_sancion)
    except ValueError:
        print("❌ ID de sanción inválido.")
        return
    
    confirmacion = input(f"⚠️  ¿Confirma eliminar la sanción #{id_sancion}? (s/n): ")
    if confirmacion.lower() != 's':
        print("❌ Operación cancelada.")
        return
    
    resultado = ejecutar_query(
        "DELETE FROM sancion_participante WHERE id_sancion = %s",
        (id_sancion,),
        commit=True
    )
    
    if resultado:
        print("✅ Sanción eliminada exitosamente.")
    else:
        print("❌ Error al eliminar sanción.")

def menu_sanciones():
    """Menú de gestión de sanciones"""
    while True:
        print("\n" + "="*50)
        print("⚠️  GESTIÓN DE SANCIONES")
        print("="*50)
        print("1. Listar sanciones")
        print("2. Crear sanción")
        print("3. Eliminar sanción")
        print("0. Volver al menú principal")
        print("-"*50)
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            listar_sanciones()
        elif opcion == '2':
            crear_sancion()
        elif opcion == '3':
            eliminar_sancion()
        elif opcion == '0':
            break
        else:
            print("❌ Opción inválida.")