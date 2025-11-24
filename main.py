#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Gestión de Reservas de Salas de Estudio
Universidad - Python + MySQL
"""

from flask import Flask
from db.connection import test_connection  # <-- usa tu código correcto
from modules import reservas, participantes, salas, sanciones, reportes

app = Flask(__name__)

@app.route("/")
def index():
    return {"status": "OK", "message": "Backend funcionando dentro de Docker"}

if __name__ == "__main__":
    print("🔧 Probando conexión a MySQL desde main.py...")
    test_connection()  # Esto imprime ENTORNO DOCKER y prueba conexión
    print("✔ Backend iniciado")

    # Importante: escuchar en 0.0.0.0 para Docker
    app.run(host="0.0.0.0", port=5000, debug=True)


# ============= PUNTO DE ENTRADA =============

if __name__ == "__main__":
    # Verificar conexión
    conn = conectar()
    if conn:
        print("✅ Conexión a MySQL establecida correctamente.")
        conn.close()
        menu_principal()
    else:
        print("❌ No se pudo conectar a MySQL. Verifique la configuración.")
        sys.exit(1)