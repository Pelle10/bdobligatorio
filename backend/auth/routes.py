from flask import Blueprint, request, jsonify, _request_ctx_stack
import bcrypt, jwt, datetime
from db import get_conn
from config import SECRET_KEY, JWT_ALG
from functools import wraps

bp = Blueprint('auth', __name__, url_prefix='/auth')

def derive_role_from_participante(email):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute('SELECT p.ci FROM participante p WHERE p.email = %s LIMIT 1', (email,))
        row = cur.fetchone()
        if not row:
            return 'alumno'
        ci = row['ci']
        cur.execute('SELECT COUNT(*) AS cnt FROM participante_programa_academico WHERE ci_participante = %s AND rol = "docente"', (ci,))
        if cur.fetchone()['cnt'] > 0:
            return 'docente'
        cur.execute("""
            SELECT COUNT(*) AS cnt 
            FROM participante_programa_academico ppa 
            JOIN programa_academico pa ON ppa.id_programa = pa.id_programa 
            WHERE ppa.ci_participante = %s AND pa.tipo = 'posgrado'
        """, (ci,))
        if cur.fetchone()['cnt'] > 0:
            return 'posgrado'
        return 'alumno'
    finally:
        cur.close()
        conn.close()

@bp.route('/register', methods=['POST'])
def register():
    data = request.json
    ci = data.get('ci')
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'alumno')

    if not all([ci, nombre, apellido, email, password]):
        return jsonify({'error': 'Datos incompletos'}), 400

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO participante (ci,nombre,apellido,email) VALUES (%s,%s,%s,%s)', (ci,nombre,apellido,email))
        cur.execute('INSERT INTO login (email, password, role) VALUES (%s,%s,%s)', (email, pw_hash, role))
        conn.commit()
        return jsonify({'ok': True}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        cur.close()
        conn.close()

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email y password requeridos'}), 400

    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT password, role FROM login WHERE email=%s', (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({'error': 'Credenciales inválidas'}), 401

    pw_hash = row['password'].encode()
    if not bcrypt.checkpw(password.encode(), pw_hash):
        return jsonify({'error': 'Credenciales inválidas'}), 401

    role = row.get('role') or derive_role_from_participante(email)
    payload = {
        'sub': email,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALG)
    return jsonify({'token': token, 'role': role})

def require_role(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth = request.headers.get('Authorization', None)
            if not auth or not auth.startswith('Bearer '):
                return jsonify({'error': 'Token requerido'}), 401

            token = auth.split(None, 1)[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALG])
                user_role = payload.get('role', 'alumno')

                if user_role not in allowed_roles:
                    return jsonify({'error': 'Permiso denegado'}), 403

                # Guardamos el usuario actual en el contexto de Flask
                _request_ctx_stack.top.current_user = payload.get('sub')

            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expirado'}), 401
            except jwt.InvalidTokenError as e:
                return jsonify({'error': 'Token inválido', 'detail': str(e)}), 401
            except Exception as e:
                return jsonify({'error': 'Error al procesar token', 'detail': str(e)}), 500

            return f(*args, **kwargs)
        return wrapped
    return decorator