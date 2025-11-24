-- Script de datos de ejemplo para Sistema de Reservas de Salas
-- Encoding: UTF-8
USE reserva_salas;

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Datos de login (contraseñas: 'password123' con bcrypt)
INSERT INTO login (correo, contrasena) VALUES
('juan.perez@uni.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILSa8jW8u'),
('maria.gomez@uni.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILSa8jW8u'),
('carlos.rodriguez@uni.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILSa8jW8u'),
('ana.martinez@uni.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILSa8jW8u'),
('luis.fernandez@uni.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILSa8jW8u'),
('sofia.lopez@uni.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILSa8jW8u'),
('pedro.sanchez@uni.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILSa8jW8u'),
('laura.garcia@uni.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILSa8jW8u');

-- Datos de facultad
INSERT INTO facultad (nombre) VALUES
('Facultad de Ingeniería'),
('Facultad de Ciencias Sociales'),
('Facultad de Medicina'),
('Facultad de Derecho');

-- Datos de programa_academico
INSERT INTO programa_academico (nombre_programa, id_facultad, tipo) VALUES
('Ingeniería en Sistemas', 1, 'grado'),
('Ingeniería Civil', 1, 'grado'),
('Maestría en Ingeniería de Software', 1, 'posgrado'),
('Psicología', 2, 'grado'),
('Doctorado en Ciencias Sociales', 2, 'posgrado'),
('Medicina', 3, 'grado'),
('Derecho', 4, 'grado');

-- Datos de participante
INSERT INTO participante (ci, nombre, apellido, email) VALUES
('12345678', 'Juan', 'Pérez', 'juan.perez@uni.edu'),
('23456789', 'María', 'Gómez', 'maria.gomez@uni.edu'),
('34567890', 'Carlos', 'Rodríguez', 'carlos.rodriguez@uni.edu'),
('45678901', 'Ana', 'Martínez', 'ana.martinez@uni.edu'),
('56789012', 'Luis', 'Fernández', 'luis.fernandez@uni.edu'),
('67890123', 'Sofía', 'López', 'sofia.lopez@uni.edu'),
('78901234', 'Pedro', 'Sánchez', 'pedro.sanchez@uni.edu'),
('89012345', 'Laura', 'García', 'laura.garcia@uni.edu');

-- Datos de participante_programa_academico
INSERT INTO participante_programa_academico (ci_participante, nombre_programa, rol) VALUES
('12345678', 'Ingeniería en Sistemas', 'alumno'),
('23456789', 'Ingeniería Civil', 'alumno'),
('34567890', 'Maestría en Ingeniería de Software', 'alumno'),
('45678901', 'Psicología', 'alumno'),
('56789012', 'Ingeniería en Sistemas', 'docente'),
('67890123', 'Doctorado en Ciencias Sociales', 'alumno'),
('78901234', 'Medicina', 'docente'),
('89012345', 'Derecho', 'alumno');

-- Datos de edificio
INSERT INTO edificio (nombre_edificio, direccion, departamento) VALUES
('Edificio Central', 'Av. Principal 1234', 'Montevideo'),
('Edificio Norte', 'Calle Norte 567', 'Montevideo'),
('Edificio Sur', 'Calle Sur 890', 'Canelones');

-- Datos de sala
INSERT INTO sala (nombre_sala, edificio, capacidad, tipo_sala) VALUES
('Sala 101', 'Edificio Central', 6, 'libre'),
('Sala 102', 'Edificio Central', 8, 'libre'),
('Sala 201', 'Edificio Central', 4, 'posgrado'),
('Sala 301', 'Edificio Central', 10, 'docente'),
('Sala A1', 'Edificio Norte', 6, 'libre'),
('Sala A2', 'Edificio Norte', 8, 'libre'),
('Sala B1', 'Edificio Norte', 5, 'posgrado'),
('Sala C1', 'Edificio Sur', 12, 'libre'),
('Sala C2', 'Edificio Sur', 6, 'docente');

-- Datos de turno 
INSERT INTO turno (hora_inicio, hora_fin) VALUES
('08:00:00', '09:00:00'),
('09:00:00', '10:00:00'),
('10:00:00', '11:00:00'),
('11:00:00', '12:00:00'),
('12:00:00', '13:00:00'),
('13:00:00', '14:00:00'),
('14:00:00', '15:00:00'),
('15:00:00', '16:00:00'),
('16:00:00', '17:00:00'),
('17:00:00', '18:00:00'),
('18:00:00', '19:00:00'),
('19:00:00', '20:00:00'),
('20:00:00', '21:00:00'),
('21:00:00', '22:00:00'),
('22:00:00', '23:00:00');

-- Datos de reserva
INSERT INTO reserva (nombre_sala, edificio, fecha, id_turno, estado) VALUES
('Sala 101', 'Edificio Central', CURDATE(), 1, 'activa'),
('Sala 102', 'Edificio Central', CURDATE(), 2, 'activa'),
('Sala 201', 'Edificio Central', CURDATE(), 3, 'activa'),
('Sala A1', 'Edificio Norte', CURDATE(), 4, 'finalizada'),
('Sala A2', 'Edificio Norte', DATE_ADD(CURDATE(), INTERVAL 1 DAY), 5, 'activa'),
('Sala C1', 'Edificio Sur', DATE_ADD(CURDATE(), INTERVAL 2 DAY), 6, 'activa');

-- Datos de reserva_participante
INSERT INTO reserva_participante (ci_participante, id_reserva, asistencia) VALUES
('12345678', 1, NULL),
('23456789', 1, NULL),
('34567890', 2, NULL),
('45678901', 3, NULL),
('56789012', 4, TRUE),
('67890123', 4, TRUE),
('78901234', 5, NULL),
('89012345', 6, NULL);

-- Datos de sancion_participante (ninguna sanción activa inicialmente)
-- Se pueden agregar ejemplos de sanciones pasadas
INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin) VALUES
('12345678', DATE_SUB(CURDATE(), INTERVAL 90 DAY), DATE_SUB(CURDATE(), INTERVAL 30 DAY));