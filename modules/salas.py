#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de gestión de salas
"""

from db.connection import ejecutar_query

def listar_salas():
    """Muestra todas las salas"""
    query = """
        SELECT s.nombre_sala, s.edificio, s.capacidad, s.tipo_sala, e.direccion
        FROM sala s
        JOIN edificio e ON s.edificio = e.nombre_edificio
        ORDER BY s.edificio, s.nombre_sala
    """
    salas = ejecutar_query(query, fetchall=True)
    
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

def crear_sala():
    """Crea una nueva sala"""
    print("\n➕ CREAR SALA")
    print("-" * 50)
    
    # Listar edificios disponibles
    edificios = ejecutar_query("SELECT * FROM edificio", fetchall=True)
    if not edificios:
        print("❌ No hay edificios registrados. Cree un edificio primero.")
        return
    
    print("\nEdificios disponibles:")
    for e in edificios:
        print(f"  - {e['nombre_edificio']}")
    
    nombre_sala = input("\nNombre de la sala: ").strip()
    edificio = input("Edificio: ").strip()
    capacidad = input("Capacidad: ").strip()
    
    print("\nTipos de sala: libre, posgrado, docente")
    tipo_sala = input("Tipo de sala: ").strip().lower()
    
    # Validaciones
    if not nombre_sala or not edificio or not capacidad or not tipo_sala:
        print("❌ Todos los campos son obligatorios.")
        return
    
    if tipo_sala not in ['libre', 'posgrado', 'docente']:
        print("❌ Tipo de sala inválido.")
        return
    
    try:
        capacidad = int(capacidad)
        if capacidad <= 0:
            raise ValueError
    except ValueError:
        print("❌ La capacidad debe ser un número positivo.")
        return
    
    resultado = ejecutar_query(
        "INSERT INTO sala (nombre_sala, edificio, capacidad, tipo_sala) VALUES (%s, %s, %s, %s)",
        (nombre_sala, edificio, capacidad, tipo_sala),
        commit=True
    )
    
    if resultado:
        print(f"✅ Sala {nombre_sala} creada exitosamente.")
    else:
        print("❌ Error al crear sala.")

def modificar_sala():
    """Modifica datos de una sala"""
    listar_salas()
    
    nombre_sala = input("\nNombre de la sala a modificar: ").strip()
    edificio = input("Edificio: ").strip()
    
    sala = ejecutar_query(
        "SELECT * FROM sala WHERE nombre_sala = %s AND edificio = %s",
        (nombre_sala, edificio),
        fetchone=True
    )
    
    if not sala:
        print("❌ Sala no encontrada.")
        return
    
    print(f"\nModificando: {sala['nombre_sala']} en {sala['edificio']}")
    print("(Presione Enter para mantener el valor actual)")
    
    capacidad = input(f"Capacidad [{sala['capacidad']}]: ").strip()
    tipo_sala = input(f"Tipo [{sala['tipo_sala']}]: ").strip()
    
    capacidad = int(capacidad) if capacidad else sala['capacidad']
    tipo_sala = tipo_sala if tipo_sala else sala['tipo_sala']
    
    resultado = ejecutar_query(
        "UPDATE sala SET capacidad = %s, tipo_sala = %s WHERE nombre_sala = %s AND edificio = %s",
        (capacidad, tipo_sala, nombre_sala, edificio),
        commit=True
    )
    
    if resultado:
        print("✅ Sala actualizada exitosamente.")
    else:
        print("❌ Error al actualizar sala.")

def eliminar_sala():
    """Elimina una sala"""
    listar_salas()
    
    nombre_sala = input("\nNombre de la sala a eliminar: ").strip()
    edificio = input("Edificio: ").strip()
    
    confirmacion = input(f"⚠️  ¿Confirma eliminar la sala {nombre_sala} en {edificio}? (s/n): ")
    if confirmacion.lower() != 's':
        print("❌ Operación cancelada.")
        return
    
    resultado = ejecutar_query(
        "DELETE FROM sala WHERE nombre_sala = %s AND edificio = %s",
        (nombre_sala, edificio),
        commit=True
    )
    
    if resultado:
        print("✅ Sala eliminada exitosamente.")
    else:
        print("❌ Error al eliminar sala.")

def menu_salas():
    """Menú de gestión de salas"""
    while True:
        print("\n" + "="*50)
        print("🏢 GESTIÓN DE SALAS")
        print("="*50)
        print("1. Listar salas")
        print("2. Crear sala")
        print("3. Modificar sala")
        print("4. Eliminar sala")
        print("0. Volver al menú principal")
        print("-"*50)
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            listar_salas()
        elif opcion == '2':
            crear_sala()
        elif opcion == '3':
            modificar_sala()
        elif opcion == '4':
            eliminar_sala()
        elif opcion == '0':
            break
        else:
            print("❌ Opción inválida.")