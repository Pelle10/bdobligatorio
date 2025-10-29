import os
SECRET_KEY = os.getenv('SECRET_KEY','cambiame_ya_en_prod')
JWT_ALG = 'HS256'
DB_CONFIG = {
    'host': os.getenv('DB_HOST','localhost'),
    'user': os.getenv('DB_USER','app_user'),
    'password': os.getenv('DB_PASS','app_pass'),
    'database': os.getenv('DB_NAME','reserva_salas')
}
