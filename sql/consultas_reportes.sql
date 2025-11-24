-- =====================================================
-- CONSULTAS SQL PARA REPORTES Y ANÁLISIS BI
-- Sistema de Gestión de Reservas de Salas
-- =====================================================

USE reserva_salas;

-- =====================================================
-- CONSULTA 1: Salas Más Reservadas
-- Propósito: Identificar qué salas tienen mayor demanda
-- =====================================================

SELECT 
    s.nombre_sala,
    s.edificio,
    s.capacidad,
    s.tipo_sala,
    COUNT(r.id_reserva) as total_reservas
FROM sala s
LEFT JOIN reserva r ON s.nombre_sala = r.nombre_sala 
                    AND s.edificio = r.edificio
GROUP BY s.nombre_sala, s.edificio, s.capacidad, s.tipo_sala
ORDER BY total_reservas DESC
LIMIT 10;

-- =====================================================
-- CONSULTA 2: Turnos Más Demandados
-- Propósito: Identificar los horarios más solicitados
-- =====================================================

SELECT 
    t.id_turno,
    CONCAT(t.hora_inicio, ' - ', t.hora_fin) as horario,
    COUNT(r.id_reserva) as total_reservas
FROM turno t
LEFT JOIN reserva r ON t.id_turno = r.id_turno
GROUP BY t.id_turno, t.hora_inicio, t.hora_fin
ORDER BY total_reservas DESC;

-- =====================================================
-- CONSULTA 3: Promedio de Participantes por Sala
-- Propósito: Analizar la ocupación promedio de cada sala
-- =====================================================

SELECT 
    s.nombre_sala,
    s.edificio,
    s.capacidad,
    COALESCE(AVG(participantes.num_part), 0) as promedio_participantes,
    ROUND(COALESCE(AVG(participantes.num_part), 0) * 100.0 / s.capacidad, 2) as porcentaje_capacidad
FROM sala s
LEFT JOIN (
    SELECT 
        r.nombre_sala,
        r.edificio,
        COUNT(rp.ci_participante) as num_part
    FROM reserva r
    LEFT JOIN reserva_participante rp ON r.id_reserva = rp.id_reserva
    GROUP BY r.id_reserva, r.nombre_sala, r.edificio
) participantes ON s.nombre_sala = participantes.nombre_sala
                  AND s.edificio = participantes.edificio
GROUP BY s.nombre_sala, s.edificio, s.capacidad
ORDER BY promedio_participantes DESC;

-- =====================================================
-- CONSULTA 4: Cantidad de Reservas por Carrera y Facultad
-- Propósito: Distribución de uso del sistema por programa académico
-- =====================================================

SELECT 
    f.nombre as facultad,
    pa.nombre_programa,
    pa.tipo as tipo_programa,
    COUNT(DISTINCT r.id_reserva) as total_reservas
FROM facultad f
JOIN programa_academico pa ON f.id_facultad = pa.id_facultad
LEFT JOIN participante_programa_academico ppa ON pa.nombre_programa = ppa.nombre_programa
LEFT JOIN reserva_participante rp ON ppa.ci_participante = rp.ci_participante
LEFT JOIN reserva r ON rp.id_reserva = r.id_reserva
GROUP BY f.nombre, pa.nombre_programa, pa.tipo
ORDER BY f.nombre, total_reservas DESC;

-- =====================================================
-- CONSULTA 5: Porcentaje de Ocupación de Salas por Edificio
-- Propósito: Eficiencia de uso de espacios por ubicación
-- Nota: Calcula ocupación de los últimos 30 días
-- =====================================================

SELECT 
    e.nombre_edificio,
    COUNT(DISTINCT s.nombre_sala) as total_salas,
    COUNT(r.id_reserva) as total_reservas,
    ROUND(COUNT(r.id_reserva) * 100.0 / 
          NULLIF(COUNT(DISTINCT s.nombre_sala) * 
                 (SELECT COUNT(*) FROM turno) * 30, 0), 2) as porcentaje_ocupacion
FROM edificio e
LEFT JOIN sala s ON e.nombre_edificio = s.edificio
LEFT JOIN reserva r ON s.nombre_sala = r.nombre_sala 
                    AND s.edificio = r.edificio
                    AND r.fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY e.nombre_edificio
ORDER BY porcentaje_ocupacion DESC;

-- =====================================================
-- CONSULTA 6: Reservas y Asistencias por Tipo de Usuario
-- Propósito: Comparar comportamiento entre Docentes, Alumnos de Grado y Posgrado
-- =====================================================

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
    ROUND(SUM(CASE WHEN rp.asistencia = TRUE THEN 1 ELSE 0 END) * 100.0 / 
          NULLIF(COUNT(rp.id_reserva), 0), 2) as porcentaje_asistencia
FROM participante_programa_academico ppa
JOIN programa_academico pa ON ppa.nombre_programa = pa.nombre_programa
LEFT JOIN reserva_participante rp ON ppa.ci_participante = rp.ci_participante
GROUP BY tipo_usuario
ORDER BY total_reservas DESC;

-- =====================================================
-- CONSULTA 7: Cantidad de Sanciones por Tipo de Usuario
-- Propósito: Analizar el comportamiento disciplinario por rol
-- =====================================================

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
    ROUND(AVG(DATEDIFF(sp.fecha_fin, sp.fecha_inicio)), 0) as duracion_promedio_dias
FROM sancion_participante sp
JOIN participante_programa_academico ppa ON sp.ci_participante = ppa.ci_participante
JOIN programa_academico pa ON ppa.nombre_programa = pa.nombre_programa
GROUP BY tipo_usuario
ORDER BY total_sanciones DESC;

-- =====================================================
-- CONSULTA 8: Efectividad de Reservas
-- Propósito: % de reservas utilizadas vs canceladas vs sin asistencia
-- =====================================================

SELECT 
    estado,
    COUNT(*) as total,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reserva), 2) as porcentaje
FROM reserva
GROUP BY estado
ORDER BY total DESC;

-- =====================================================
-- CONSULTA 9: Horas Reservadas por Semana
-- Propósito: Analizar tendencias temporales de uso del sistema
-- Utilidad: Identificar picos de demanda para planificación
-- =====================================================

SELECT 
    YEARWEEK(r.fecha, 1) as semana,
    YEAR(r.fecha) as anio,
    WEEK(r.fecha, 1) as num_semana,
    DATE(DATE_SUB(r.fecha, INTERVAL WEEKDAY(r.fecha) DAY)) as inicio_semana,
    COUNT(*) as total_horas_reservadas,
    COUNT(CASE WHEN estado = 'activa' THEN 1 END) as horas_activas,
    COUNT(CASE WHEN estado = 'finalizada' THEN 1 END) as horas_finalizadas,
    COUNT(CASE WHEN estado = 'cancelada' THEN 1 END) as horas_canceladas
FROM reserva r
WHERE r.fecha >= DATE_SUB(CURDATE(), INTERVAL 8 WEEK)
GROUP BY semana, anio, num_semana, inicio_semana
ORDER BY semana DESC;

-- =====================================================
-- CONSULTA 10: Participantes Más Sancionados
-- Propósito: Identificar usuarios con comportamiento recurrente problemático
-- Utilidad: Focalizar esfuerzos de seguimiento y mejora
-- =====================================================

SELECT 
    p.ci,
    p.nombre,
    p.apellido,
    p.email,
    COUNT(sp.id_sancion) as total_sanciones,
    COUNT(CASE WHEN CURDATE() BETWEEN sp.fecha_inicio AND sp.fecha_fin 
               THEN 1 END) as sanciones_activas,
    MAX(sp.fecha_fin) as ultima_sancion_fin,
    GROUP_CONCAT(DISTINCT ppa.rol ORDER BY ppa.rol SEPARATOR ', ') as roles
FROM participante p
LEFT JOIN sancion_participante sp ON p.ci = sp.ci_participante
LEFT JOIN participante_programa_academico ppa ON p.ci = ppa.ci_participante
GROUP BY p.ci, p.nombre, p.apellido, p.email
HAVING total_sanciones > 0
ORDER BY total_sanciones DESC, ultima_sancion_fin DESC
LIMIT 10;

-- =====================================================
-- CONSULTA 11: Edificios con Más Cancelaciones
-- Propósito: Detectar problemas de infraestructura o accesibilidad por ubicación
-- Utilidad: Priorizar inversiones en mejoras de edificios
-- =====================================================

SELECT 
    e.nombre_edificio,
    e.direccion,
    COUNT(r.id_reserva) as total_reservas,
    COUNT(CASE WHEN r.estado = 'cancelada' THEN 1 END) as total_canceladas,
    COUNT(CASE WHEN r.estado = 'sin asistencia' THEN 1 END) as total_sin_asistencia,
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