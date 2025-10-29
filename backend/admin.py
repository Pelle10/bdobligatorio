from flask import Blueprint, jsonify
from db import get_conn
from auth import require_role

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/trigger_check_no_show', methods=['POST'])
@require_role('admin')
def trigger_check_no_show():
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute('CALL marcar_reservas_sin_asistencia()')
        conn.commit()
        return jsonify({'ok': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close(); conn.close()
