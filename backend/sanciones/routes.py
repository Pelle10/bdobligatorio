from flask import Blueprint, request, jsonify
from db import get_conn

bp = Blueprint('sanciones', __name__, url_prefix='/sanciones')

@bp.route('/<ci>', methods=['GET'])
def list_sanciones(ci):
    conn = get_conn(); cur = conn.cursor(dictionary=True)
    cur.execute('SELECT id_sancion, ci_participante, fecha_inicio, fecha_fin, motivo FROM sancion_participante WHERE ci_participante=%s ORDER BY fecha_inicio DESC', (ci,))
    rows = cur.fetchall(); cur.close(); conn.close()
    return jsonify(rows)

@bp.route('', methods=['POST'])
def create_sancion():
    data = request.json
    ci = data.get('ci'); fi = data.get('fecha_inicio'); ff = data.get('fecha_fin'); motivo = data.get('motivo','')
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute('CALL sp_create_sancion(%s,%s,%s,%s)', (ci, fi, ff, motivo))
        conn.commit()
        return jsonify({'ok':True}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        cur.close(); conn.close()
