-- =====================================================
-- VISTAS PARA REPORTES Y CONSULTAS BI
-- Sistema de Gestión de Reservas de Salas
-- =====================================================

USE reservas_salas;

-- Eliminar vistas existentes si existen
DROP VIEW IF EXISTS v_salas_mas_reservadas;
DROP VIEW IF EXISTS v_turnos_mas_demandados;
DROP VIEW IF EXISTS v_promedio_participantes_sala;
DROP VIEW IF EXISTS v_reservas_por_carrera_facultad;
DROP VIEW IF EXISTS v_ocupacion_por_edificio;
DROP VIEW IF EXISTS v_reservas_asistencias_por_tipo;
DROP VIEW IF EXISTS v_sanciones_por_tipo_usuario;
DROP VIEW IF EXISTS v_efectividad_reservas;
DROP VIEW IF EXISTS v_horas_reservadas_por_semana;
DROP VIEW IF EXISTS v_participantes_mas_sancionados;
DROP VIEW IF EXISTS v_edificios_mas_cancelaciones;

-- =====================================================
-- VISTA 1: Salas Más Reservadas
-- =====================================================
CREATE VIEW v_salas_mas_reservadas AS
SELECT 
    s.nombre_sala,
    s.edificio,
    s.capacidad,
    s.tipo_sala,
    COUNT(r.id_reserva) as total_reservas,
    COUNT(CASE WHEN r.estado = 'activa' THEN 1 END) as reservas_activas,
    COUNT(CASE WHEN r.estado = 'finalizada' THEN 1 END) as reservas_finalizadas
FROM sala s
LEFT JOIN reserva r ON s.nombre_sala = r.nombre_sala 
                    AND s.edificio = r.edificio
GROUP BY s.nombre_sala, s.edificio, s.capacidad, s.tipo_sala
ORDER BY total_reservas DESC;

-- =====================================================
-- VISTA 2: Turnos Más Demandados
-- =====================================================
CREATE VIEW v_turnos_mas_demandados AS
SELECT 
    t.id_turno,
    t.hora_inicio,
    t.hora_fin,
    CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario,
    COUNT(r.id_reserva) as total_reservas,
    COUNT(CASE WHEN r.estado = 'activa' THEN 1 END) as reservas_activas,
    ROUND(COUNT(r.id_reserva) * 100.0 / 
          NULLIF((SELECT COUNT(*) FROM reserva), 0), 2) as porcentaje_total
FROM turno t
LEFT JOIN reserva r ON t.id_turno = r.id_turno
GROUP BY t.id_turno, t.hora_inicio, t.hora_fin
ORDER BY total_reservas DESC;

-- =====================================================
-- VISTA 3: Promedio de Participantes por Sala
-- =====================================================
CREATE VIEW v_promedio_participantes_sala AS
SELECT 
    s.nombre_sala,
    s.edificio,
    s.capacidad,
    COUNT(DISTINCT r.id_reserva) as total_reservas,
    COALESCE(AVG(participantes.num_part), 0) as promedio_participantes,
    ROUND(COALESCE(AVG(participantes.num_part), 0) * 100.0 / s.capacidad, 2) as porcentaje_ocupacion_promedio
FROM sala s
LEFT JOIN reserva r ON s.nombre_sala = r.nombre_sala 
                    AND s.edificio = r.edificio
LEFT JOIN (
    SELECT 
        r2.id_reserva,
        r2.nombre_sala,
        r2.edificio,
        COUNT(rp.ci_participante) as num_part
    FROM reserva r2
    LEFT JOIN reserva_participante rp ON r2.id_reserva = rp.id_reserva
    GROUP BY r2.id_reserva, r2.nombre_sala, r2.edificio
) participantes ON r.id_reserva = participantes.id_reserva
GROUP BY s.nombre_sala, s.edificio, s.capacidad
ORDER BY promedio_participantes DESC;

-- =====================================================
-- VISTA 4: Reservas por Carrera y Facultad
-- =====================================================
CREATE VIEW v_reservas_por_carrera_facultad AS
SELECT 
    f.id_facultad,
    f.nombre as facultad,
    pa.nombre_programa,
    pa.tipo as tipo_programa,
    COUNT(DISTINCT ppa.ci_participante) as total_participantes,
    COUNT(DISTINCT r.id_reserva) as total_reservas,
    COUNT(CASE WHEN r.estado = 'activa' THEN 1 END) as reservas_activas,
    COUNT(CASE WHEN r.estado = 'finalizada' THEN 1 END) as reservas_finalizadas,
    COUNT(CASE WHEN r.estado = 'cancelada' THEN 1 END) as reservas_canceladas
FROM facultad f
JOIN programa_academico pa ON f.id_facultad = pa.id_facultad
LEFT JOIN participante_programa_academico ppa ON pa.nombre_programa = ppa.nombre_programa
LEFT JOIN reserva_participante rp ON ppa.ci_participante = rp.ci_participante
LEFT JOIN reserva r ON rp.id_reserva = r.id_reserva
GROUP BY f.id_facultad, f.nombre, pa.nombre_programa, pa.tipo
ORDER BY f.nombre, total_reservas DESC;

-- =====================================================
-- VISTA 5: Porcentaje de Ocupación por Edificio
-- =====================================================
CREATE VIEW v_ocupacion_por_edificio AS
SELECT 
    e.nombre_edificio,
    e.direccion,
    e.departamento,
    COUNT(DISTINCT s.nombre_sala) as total_salas,
    SUM(s.capacidad) as capacidad_total,
    COUNT(r.id_reserva) as total_reservas_30dias,
    COUNT(CASE WHEN r.estado = 'activa' THEN 1 END) as reservas_activas,
    ROUND(COUNT(r.id_reserva) * 100.0 / 
          NULLIF(COUNT(DISTINCT s.nombre_sala) * 
                 (SELECT COUNT(*) FROM turno) * 30, 0), 2) as porcentaje_ocupacion
FROM edificio e
LEFT JOIN sala s ON e.nombre_edificio = s.edificio
LEFT JOIN reserva r ON s.nombre_sala = r.nombre_sala 
                    AND s.edificio = r.edificio
                    AND r.fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY e.nombre_edificio, e.direccion, e.departamento
ORDER BY porcentaje_ocupacion DESC;

-- =====================================================
-- VISTA 6: Reservas y Asistencias por Tipo de Usuario
-- =====================================================
CREATE VIEW v_reservas_asistencias_por_tipo AS
SELECT 
    CASE 
        WHEN ppa.rol = 'docente' THEN 'Docente'
        WHEN pa.tipo = 'posgrado' THEN 'Alumno Posgrado'
        ELSE 'Alumno Grado'
    END as tipo_usuario,
    COUNT(DISTINCT ppa.ci_participante) as total_usuarios,
    COUNT(DISTINCT rp.id_reserva) as total_reservas,
    SUM(CASE WHEN rp.asistencia = TRUE THEN 1 ELSE 0 END) as total_asistencias,
    SUM(CASE WHEN rp.asistencia = FALSE THEN 1 ELSE 0 END) as total_inasistencias,
    SUM(CASE WHEN rp.asistencia IS NULL THEN 1 ELSE 0 END) as pendientes_registro,
    ROUND(SUM(CASE WHEN rp.asistencia = TRUE THEN 1 ELSE 0 END) * 100.0 / 
          NULLIF(COUNT(rp.id_reserva), 0), 2) as porcentaje_asistencia
FROM participante_programa_academico ppa
JOIN programa_academico pa ON ppa.nombre_programa = pa.nombre_programa
LEFT JOIN reserva_participante rp ON ppa.ci_participante = rp.ci_participante
GROUP BY tipo_usuario
ORDER BY total_reservas DESC;

-- =====================================================
-- VISTA 7: Sanciones por Tipo de Usuario
-- =====================================================
CREATE VIEW v_sanciones_por_tipo_usuario AS
SELECT 
    CASE 
        WHEN ppa.rol = 'docente' THEN 'Docente'
        WHEN pa.tipo = 'posgrado' THEN 'Alumno Posgrado'
        ELSE 'Alumno Grado'
    END as tipo_usuario,
    COUNT(DISTINCT sp.ci_participante) as usuarios_sancionados,
    COUNT(sp.id_sancion) as total_sanciones,
    COUNT(CASE WHEN CURDATE() BETWEEN sp.fecha_inicio AND sp.fecha_fin 
               THEN 1 END) as sanciones_activas,
    COUNT(CASE WHEN CURDATE() > sp.fecha_fin 
               THEN 1 END) as sanciones_finalizadas,
    ROUND(AVG(DATEDIFF(sp.fecha_fin, sp.fecha_inicio)), 0) as duracion_promedio_dias
FROM sancion_participante sp
JOIN participante_programa_academico ppa ON sp.ci_participante = ppa.ci_participante
JOIN programa_academico pa ON ppa.nombre_programa = pa.nombre_programa
GROUP BY tipo_usuario
ORDER BY total_sanciones DESC;

-- =====================================================
-- VISTA 8: Efectividad de Reservas
-- =====================================================
CREATE VIEW v_efectividad_reservas AS
SELECT 
    estado,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reserva), 2) as porcentaje,
    COUNT(CASE WHEN fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) 
               THEN 1 END) as ultimos_30_dias,
    COUNT(CASE WHEN fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) 
               THEN 1 END) as ultimos_7_dias
FROM reserva
GROUP BY estado
ORDER BY total DESC;

-- =====================================================
-- VISTA 9: Horas Reservadas por Semana
-- =====================================================
CREATE VIEW v_horas_reservadas_por_semana AS
SELECT 
    YEARWEEK(r.fecha, 1) as semana,
    YEAR(r.fecha) as anio,
    WEEK(r.fecha, 1) as num_semana,
    DATE(DATE_SUB(r.fecha, INTERVAL WEEKDAY(r.fecha) DAY)) as inicio_semana,
    DATE(DATE_ADD(DATE_SUB(r.fecha, INTERVAL WEEKDAY(r.fecha) DAY), INTERVAL 6 DAY)) as fin_semana,
    COUNT(*) as total_horas_reservadas,
    COUNT(CASE WHEN estado = 'activa' THEN 1 END) as horas_activas,
    COUNT(CASE WHEN estado = 'finalizada' THEN 1 END) as horas_finalizadas,
    COUNT(CASE WHEN estado = 'cancelada' THEN 1 END) as horas_canceladas
FROM reserva r
WHERE r.fecha >= DATE_SUB(CURDATE(), INTERVAL 12 WEEK)
GROUP BY semana, anio, num_semana, inicio_semana, fin_semana
ORDER BY semana DESC;

-- =====================================================
-- VISTA 10: Participantes Más Sancionados
-- =====================================================
CREATE VIEW v_participantes_mas_sancionados AS
SELECT 
    p.ci,
    p.nombre,
    p.apellido,
    p.email,
    COUNT(sp.id_sancion) as total_sanciones,
    COUNT(CASE WHEN CURDATE() BETWEEN sp.fecha_inicio AND sp.fecha_fin 
               THEN 1 END) as sanciones_activas,
    MAX(sp.fecha_fin) as ultima_sancion_fin,
    MIN(sp.fecha_inicio) as primera_sancion_inicio,
    ROUND(AVG(DATEDIFF(sp.fecha_fin, sp.fecha_inicio)), 0) as duracion_promedio_dias,
    GROUP_CONCAT(DISTINCT ppa.rol ORDER BY ppa.rol SEPARATOR ', ') as roles
FROM participante p
LEFT JOIN sancion_participante sp ON p.ci = sp.ci_participante
LEFT JOIN participante_programa_academico ppa ON p.ci = ppa.ci_participante
GROUP BY p.ci, p.nombre, p.apellido, p.email
HAVING total_sanciones > 0
ORDER BY total_sanciones DESC, ultima_sancion_fin DESC;

-- =====================================================
-- VISTA 11: Edificios con Más Cancelaciones
-- =====================================================
CREATE VIEW v_edificios_mas_cancelaciones AS
SELECT 
    e.nombre_edificio,
    e.direccion,
    COUNT(r.id_reserva) as total_reservas,
    COUNT(CASE WHEN r.estado = 'cancelada' THEN 1 END) as total_canceladas,
    COUNT(CASE WHEN r.estado = 'sin asistencia' THEN 1 END) as total_sin_asistencia,
    COUNT(CASE WHEN r.estado = 'finalizada' THEN 1 END) as total_finalizadas,
    COUNT(CASE WHEN r.estado = 'activa' THEN 1 END) as total_activas,
    ROUND(COUNT(CASE WHEN r.estado = 'cancelada' THEN 1 END) * 100.0 / 
          NULLIF(COUNT(r.id_reserva), 0), 2) as porcentaje_cancelacion,
    ROUND((COUNT(CASE WHEN r.estado = 'cancelada' THEN 1 END) + 
           COUNT(CASE WHEN r.estado = 'sin asistencia' THEN 1 END)) * 100.0 / 
          NULLIF(COUNT(r.id_reserva), 0), 2) as porcentaje_problematicas
FROM edificio e
LEFT JOIN sala s ON e.nombre_edificio = s.edificio
LEFT JOIN reserva r ON s.nombre_sala = r.nombre_sala 
                    AND s.edificio = r.edificio
GROUP BY e.nombre_edificio, e.direccion
HAVING total_reservas > 0
ORDER BY total_canceladas DESC, porcentaje_cancelacion DESC;

-- =====================================================
-- Verificar creación de vistas
-- =====================================================
SELECT 
    TABLE_NAME as vista,
    TABLE_COMMENT as comentario
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'reservas_salas' 
  AND TABLE_TYPE = 'VIEW'
ORDER BY TABLE_NAME;
