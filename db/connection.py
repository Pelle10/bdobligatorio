#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de conexión a base de datos MySQL
"""

import mysql.connector
from mysql.connector import Error
import os

# Configuración de conexión (puede usar variables de entorno)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3307')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'reserva_salas'),
    'charset': 'utf8mb4'
}

def conectar():
    """Establece conexión con MySQL"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # Asegurar UTF-8 en la conexión
        cursor = conn.cursor()
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")
        cursor.close()
        return conn
    except Error as e:
        print(f"❌ Error al conectar con MySQL: {e}")
        return None

def ejecutar_query(query, params=None, fetchall=False, fetchone=False, commit=False):
    """Ejecuta una query SQL y retorna resultados"""
    conn = conectar()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if commit:
            conn.commit()
            return cursor.lastrowid
        elif fetchall:
            return cursor.fetchall()
        elif fetchone:
            return cursor.fetchone()
        return True
    except Error as e:
        print(f"❌ Error en query: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def test_connection():
    """Prueba la conexión a la base de datos"""
    conn = conectar()
    if conn:
        print("✅ Conexión a MySQL establecida correctamente.")
        conn.close()
        return True
    else:
        print("❌ No se pudo conectar a MySQL. Verifique la configuración.")
        return False