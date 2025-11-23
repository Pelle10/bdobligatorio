#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de gestión de participantes
"""

import bcrypt
from db.connection import ejecutar_query, conectar
from mysql.connector import Error

def listar_participantes():
    """Muestra todos los participantes"""
    query = """
        SELECT p.ci, p.nombre, p.apellido, p.email,
               GROUP_CONCAT(CONCAT(ppa.rol, ' en ', ppa.nombre_programa) SEPARATOR ', ') as programas
        FROM participante p
        LEFT JOIN participante_programa_academico ppa ON p.ci = ppa.ci_participante
        GROUP BY p.ci, p.nombre, p.apellido, p.email
        ORDER BY p.apellido, p.nombre
    """
    participantes = ejecutar_query(query, fetchall=True)
    
    if not participantes:
        print("\n📋 No hay participantes registrados.")
        return
    
    print("\n" + "="*100)
    print("📋 LISTA DE PARTICIPANTES")
    print("="*100)
    print(f"{'CI':<12} {'Nombre':<20} {'Apellido':<20} {'Email':<30} {'Programas':<30}")
    print("-"*100)
    
    for p in participantes:
        programas = p['programas'] if p['programas'] else 'Sin programa'
        print(f"{p['ci']:<12} {p['nombre']:<20} {p['apellido']:<20} {p['email']:<30} {programas:<30}")
    print("="*100)

def crear_participante():
    """Crea un nuevo participante"""
    print("\n➕ CREAR PARTICIPANTE")
    print("-" * 50)
    
    ci = input("CI (sin puntos ni guiones): ").strip()
    nombre = input("Nombre: ").strip()
    apellido = input("Apellido: ").strip()
    email = input("Email: ").strip()
    password = input("Contraseña: ").strip()
    
    # Validaciones
    if not ci or not nombre or not apellido or not email or not password:
        print("❌ Todos los campos son obligatorios.")
        return
    
    # Hash de contraseña
    hash_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = conectar()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Insertar login
        cursor.execute("INSERT INTO login (correo, contrasena) VALUES (%s, %s)", (email, hash_pass))
        
        # Insertar participante
        cursor.execute(
            "INSERT INTO participante (ci, nombre, apellido, email) VALUES (%s, %s, %s, %s)",
            (ci, nombre, apellido, email)
        )
        
        conn.commit()
        print(f"✅ Participante {nombre} {apellido} creado exitosamente.")
        
    except Error as e:
        conn.rollback()
        print(f"❌ Error al crear participante: {e}")
    finally:
        cursor.close()
        conn.close()

def modificar_participante():
    """Modifica datos de un participante"""
    listar_participantes()
    
    ci = input("\nCI del participante a modificar: ").strip()
    
    participante = ejecutar_query(
        "SELECT * FROM participante WHERE ci = %s",
        (ci,),
        fetchone=True
    )
    
    if not participante:
        print("❌ Participante no encontrado.")
        return
    
    print(f"\nModificando: {participante['nombre']} {participante['apellido']}")
    print("(Presione Enter para mantener el valor actual)")
    
    nombre = input(f"Nombre [{participante['nombre']}]: ").strip() or participante['nombre']
    apellido = input(f"Apellido [{participante['apellido']}]: ").strip() or participante['apellido']
    
    resultado = ejecutar_query(
        "UPDATE participante SET nombre = %s, apellido = %s WHERE ci = %s",
        (nombre, apellido, ci),
        commit=True
    )
    
    if resultado:
        print("✅ Participante actualizado exitosamente.")
    else:
        print("❌ Error al actualizar participante.")

def eliminar_participante():
    """Elimina un participante"""
    listar_participantes()
    
    ci = input("\nCI del participante a eliminar: ").strip()
    
    confirmacion = input(f"⚠️  ¿Confirma eliminar al participante con CI {ci}? (s/n): ")
    if confirmacion.lower() != 's':
        print("❌ Operación cancelada.")
        return
    
    resultado = ejecutar_query(
        "DELETE FROM participante WHERE ci = %s",
        (ci,),
        commit=True
    )
    
    if resultado:
        print("✅ Participante eliminado exitosamente.")
    else:
        print("❌ Error al eliminar participante.")

def menu_participantes():
    """Menú de gestión de participantes"""
    while True:
        print("\n" + "="*50)
        print("👥 GESTIÓN DE PARTICIPANTES")
        print("="*50)
        print("1. Listar participantes")
        print("2. Crear participante")
        print("3. Modificar participante")
        print("4. Eliminar participante")
        print("0. Volver al menú principal")
        print("-"*50)
        
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            listar_participantes()
        elif opcion == '2':
            crear_participante()
        elif opcion == '3':
            modificar_participante()
        elif opcion == '4':
            eliminar_participante()
        elif opcion == '0':
            break
        else:
            print("❌ Opción inválida.")