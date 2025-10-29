from flask import Blueprint, request, jsonify
from db import get_conn
from mysql.connector import IntegrityError

bp = Blueprint('reservas', __name__, url_prefix='/reservas')

def create_reserva_atomic(conn, id_sala, fecha, id_turno, participantes_ci):
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute('SELECT COUNT(*) cnt FROM reserva WHERE id_sala=%s AND fecha=%s AND id_turno=%s FOR UPDATE', (id_sala, fecha, id_turno))
        if cur.fetchone()['cnt'] > 0:
            raise Exception('La sala ya estÃ¡ reservada en ese turno')
        cur.execute('INSERT INTO reserva (id_sala, fecha, id_turno) VALUES (%s,%s,%s)', (id_sala, fecha, id_turno))
        id_reserva = cur.lastrowid
        cur.execute('SELECT capacidad, tipo_sala FROM sala WHERE id_sala=%s', (id_sala,))
        sala = cur.fetchone()
        if not sala:
            raise Exception('Sala inexistente')
        if len(participantes_ci) > sala['capacidad']:
            raise Exception('Excede capacidad')
        for ci in participantes_ci:
            cur.execute(\"\"\"SELECT SUM(ppa.rol='docente') is_docente, SUM(pa.tipo='posgrado') is_pos FROM participante_programa_academico ppa JOIN programa_academico pa ON ppa.id_programa = pa.id_programa WHERE ppa.ci_participante = %s\"\"\", (ci,))
            r = cur.fetchone() or {'is_docente':0, 'is_pos':0}
            is_doc = r['is_docente']>0
            is_pos = r['is_pos']>0
            if sala['tipo_sala']=='docente' and not is_doc:
                raise Exception(f'Participante {ci} no puede reservar sala docente')
            if sala['tipo_sala']=='posgrado' and not (is_doc or is_pos):
                raise Exception(f'Participante {ci} no puede reservar sala posgrado')
            if not is_doc and not is_pos:
                cur.execute(\"\"\"SELECT COUNT(*) cnt FROM reserva_participante rp JOIN reserva r ON rp.id_reserva = r.id_reserva WHERE rp.ci_participante=%s AND r.fecha=%s AND r.estado='activa'\"\"\", (ci, fecha))
                if cur.fetchone()['cnt'] >= 2:
                    raise Exception(f'Participante {ci} excede lÃ­mite diario')
                cur.execute(\"\"\"SELECT COUNT(*) cnt FROM reserva_participante rp JOIN reserva r ON rp.id_reserva = r.id_reserva WHERE rp.ci_participante=%s AND YEARWEEK(r.fecha,1)=YEARWEEK(%s,1) AND r.estado='activa'\"\"\", (ci, fecha))
                if cur.fetchone()['cnt'] >= 3:
                    raise Exception(f'Participante {ci} excede lÃ­mite semanal')
        for ci in participantes_ci:
            cur.execute('INSERT INTO reserva_participante (id_reserva, ci_participante) VALUES (%s,%s)', (id_reserva, ci))
        return id_reserva
    finally:
        cur.close()

@bp.route('', methods=['POST'])
def crear_reserva():
    data = request.json
    id_sala = data.get('id_sala')
    fecha = data.get('fecha')
    id_turno = data.get('id_turno')
    participantes_ci = data.get('participantes', [])
    if not (id_sala and fecha and id_turno and participantes_ci):
        return jsonify({'error':'datos incompletos'}), 400
    conn = get_conn()
    try:
        conn.start_transaction()
        id_res = create_reserva_atomic(conn, id_sala, fecha, id_turno, participantes_ci)
        conn.commit()
        return jsonify({'ok':True, 'id_reserva': id_res}), 201
    except IntegrityError as e:
        conn.rollback()
        return jsonify({'error':'Conflicto al crear reserva: '+str(e)}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()
