-- Script de creación de base de datos para Sistema de Reservas de Salas

DROP DATABASE IF EXISTS reserva_salas;
CREATE DATABASE reserva_salas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE reserva_salas;

-- Tabla login
CREATE TABLE login (
    correo VARCHAR(100) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- Tabla facultad
CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- Tabla programa_academico
CREATE TABLE programa_academico (
    nombre_programa VARCHAR(100) PRIMARY KEY,
    id_facultad INT NOT NULL,
    tipo ENUM('grado', 'posgrado') NOT NULL,
    FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ✅ Tabla participante (SOLUCIÓN 1: FK ELIMINADA)
CREATE TABLE participante (
    ci VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE
    -- FK eliminado: ahora el correo es independiente del login
) ENGINE=InnoDB;

-- Tabla participante_programa_academico
CREATE TABLE participante_programa_academico (
    id_alumno_programa INT AUTO_INCREMENT PRIMARY KEY,
    ci_participante VARCHAR(20) NOT NULL,
    nombre_programa VARCHAR(100) NOT NULL,
    rol ENUM('alumno', 'docente') NOT NULL,
    FOREIGN KEY (ci_participante) REFERENCES participante(ci) ON DELETE CASCADE,
    FOREIGN KEY (nombre_programa) REFERENCES programa_academico(nombre_programa) ON DELETE CASCADE,
    UNIQUE KEY uk_participante_programa (ci_participante, nombre_programa)
) ENGINE=InnoDB;

-- Tabla edificio
CREATE TABLE edificio (
    nombre_edificio VARCHAR(50) PRIMARY KEY,
    direccion VARCHAR(200) NOT NULL,
    departamento VARCHAR(50) NOT NULL
) ENGINE=InnoDB;

-- Tabla sala
CREATE TABLE sala (
    nombre_sala VARCHAR(50) NOT NULL,
    edificio VARCHAR(50) NOT NULL,
    capacidad INT NOT NULL CHECK (capacidad > 0),
    tipo_sala ENUM('libre', 'posgrado', 'docente') NOT NULL,
    PRIMARY KEY (nombre_sala, edificio),
    FOREIGN KEY (edificio) REFERENCES edificio(nombre_edificio) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Tabla turno
CREATE TABLE turno (
    id_turno INT AUTO_INCREMENT PRIMARY KEY,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    CHECK (hora_inicio < hora_fin),
    CHECK (hora_inicio >= '08:00:00' AND hora_fin <= '23:00:00'),
    UNIQUE KEY uk_turno (hora_inicio, hora_fin)
) ENGINE=InnoDB;

-- Tabla reserva
CREATE TABLE reserva (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    nombre_sala VARCHAR(50) NOT NULL,
    edificio VARCHAR(50) NOT NULL,
    fecha DATE NOT NULL,
    id_turno INT NOT NULL,
    estado ENUM('activa', 'cancelada', 'sin asistencia', 'finalizada') NOT NULL DEFAULT 'activa',
    FOREIGN KEY (nombre_sala, edificio) REFERENCES sala(nombre_sala, edificio) ON DELETE RESTRICT,
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno) ON DELETE RESTRICT,
    UNIQUE KEY uk_reserva (nombre_sala, edificio, fecha, id_turno)
) ENGINE=InnoDB;

-- Tabla reserva_participante
CREATE TABLE reserva_participante (
    ci_participante VARCHAR(20) NOT NULL,
    id_reserva INT NOT NULL,
    fecha_solicitud_reserva DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    asistencia BOOLEAN DEFAULT NULL,
    PRIMARY KEY (ci_participante, id_reserva),
    FOREIGN KEY (ci_participante) REFERENCES participante(ci) ON DELETE CASCADE,
    FOREIGN KEY (id_reserva) REFERENCES reserva(id_reserva) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabla sancion_participante
CREATE TABLE sancion_participante (
    id_sancion INT AUTO_INCREMENT PRIMARY KEY,
    ci_participante VARCHAR(20) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    CHECK (fecha_fin > fecha_inicio),
    FOREIGN KEY (ci_participante) REFERENCES participante(ci) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Índices
CREATE INDEX idx_reserva_fecha ON reserva(fecha);
CREATE INDEX idx_reserva_estado ON reserva(estado);
CREATE INDEX idx_sancion_fechas ON sancion_participante(ci_participante, fecha_inicio, fecha_fin);
CREATE INDEX idx_participante_programa ON participante_programa_academico(ci_participante, rol);
