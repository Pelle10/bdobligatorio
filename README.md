# Reserva Salas - Proyecto UCU (estructura de repo)

Instrucciones rÃ¡pidas:
1. Levantar MySQL y ejecutar create_db.sql (MySQL Workbench o terminal).
2. Ajustar variables de entorno en backend/config.py o exportar env vars.
3. Instalar dependencias: pip install -r backend/requirements.txt
4. Ejecutar app: python backend/app.py
5. Ejecutar worker (opcional): python worker/notif_worker.py
6. Abrir frontend/*.html y usar auth/login para obtener token y guardarlo en localStorage.

Notas de seguridad:
- No incluir credenciales reales en el repo.
- Usar SMTP seguro y variables de entorno para secretos.
