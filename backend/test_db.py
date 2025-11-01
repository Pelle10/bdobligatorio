import mysql.connector
import os

config = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASS", ""),
    "database": os.environ.get("DB_NAME", "reserva_salas")
}

try:
    conn = mysql.connector.connect(**config)
    print("✅ Conexión a MySQL exitosa")
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    print("Tablas encontradas:", cursor.fetchall())
    conn.close()
except Exception as e:
    print("❌ Error al conectar a MySQL:", e)
