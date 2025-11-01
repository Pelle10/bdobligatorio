-- create_db.sql
-- Sistema de Reserva de Salas - UCU
-- Creación de BD, tablas, datos maestros, y triggers bÃ¡sicos para reglas de negocio
DROP DATABASE IF EXISTS reserva_salas;
CREATE DATABASE IF NOT EXISTS reserva_salas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE reserva_salas;

-- TABLAS BASE
CREATE TABLE facultad (
    id_facultad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE programa_academico (
    id_programa INT AUTO_INCREMENT PRIMARY KEY,
    nombre_programa VARCHAR(150) NOT NULL,
    id_facultad INT NOT NULL,
    tipo ENUM('grado','posgrado') NOT NULL,
    FOREIGN KEY (id_facultad) REFERENCES facultad(id_facultad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE participante (
    ci VARCHAR(15) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE login (
    email VARCHAR(150) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    role ENUM('alumno','docente','posgrado','admin') NOT NULL DEFAULT 'alumno',
    FOREIGN KEY (email) REFERENCES participante(email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE participante_programa_academico (
    id_alumno_programa INT AUTO_INCREMENT PRIMARY KEY,
    ci_participante VARCHAR(15) NOT NULL,
    id_programa INT NOT NULL,
    rol ENUM('alumno','docente') NOT NULL,
    FOREIGN KEY (ci_participante) REFERENCES participante(ci),
    FOREIGN KEY (id_programa) REFERENCES programa_academico(id_programa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE edificio (
    id_edificio INT AUTO_INCREMENT PRIMARY KEY,
    nombre_edificio VARCHAR(150) NOT NULL,
    direccion VARCHAR(200),
    departamento VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sala (
    id_sala INT AUTO_INCREMENT PRIMARY KEY,
    nombre_sala VARCHAR(100) NOT NULL,
    id_edificio INT NOT NULL,
    capacidad INT NOT NULL CHECK (capacidad > 0),
    tipo_sala ENUM('libre','posgrado','docente') NOT NULL,
    FOREIGN KEY (id_edificio) REFERENCES edificio(id_edificio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE turno (
    id_turno INT AUTO_INCREMENT PRIMARY KEY,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    UNIQUE (hora_inicio, hora_fin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE reserva (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    id_sala INT NOT NULL,
    fecha DATE NOT NULL,
    id_turno INT NOT NULL,
    estado ENUM('activa','cancelada','sin_asistencia','finalizada') NOT NULL DEFAULT 'activa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_sala) REFERENCES sala(id_sala),
    FOREIGN KEY (id_turno) REFERENCES turno(id_turno),
    UNIQUE (id_sala, fecha, id_turno)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE reserva_participante (
    id_reserva INT NOT NULL,
    ci_participante VARCHAR(15) NOT NULL,
    fecha_solicitud DATE NOT NULL DEFAULT (CURRENT_DATE),
    asistencia BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id_reserva, ci_participante),
    FOREIGN KEY (id_reserva) REFERENCES reserva(id_reserva) ON DELETE CASCADE,
    FOREIGN KEY (ci_participante) REFERENCES participante(ci)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sancion_participante (
    id_sancion INT AUTO_INCREMENT PRIMARY KEY,
    ci_participante VARCHAR(15) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    motivo VARCHAR(200),
    FOREIGN KEY (ci_participante) REFERENCES participante(ci)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notificacion (
    id_notif INT AUTO_INCREMENT PRIMARY KEY,
    ci_participante VARCHAR(15) NULL,
    tipo ENUM('sancion','sin_asistencia','recordatorio','info') NOT NULL,
    asunto VARCHAR(200) NOT NULL,
    cuerpo TEXT NOT NULL,
    destinatario_email VARCHAR(150) NULL,
    estado ENUM('pendiente','enviado','error') DEFAULT 'pendiente',
    intentos INT DEFAULT 0,
    max_intentos INT DEFAULT 5,
    last_error TEXT NULL,
    next_intento_at DATETIME DEFAULT NULL,
    creado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enviado_at DATETIME NULL,
    FOREIGN KEY (ci_participante) REFERENCES participante(ci)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- DATOS MAESTROS DE EJEMPLO
INSERT INTO facultad (nombre) VALUES
('IngenierÃ­a'), ('Ciencias Empresariales'), ('Derecho');

INSERT INTO programa_academico (nombre_programa, id_facultad, tipo) VALUES
('IngenierÃ­a en InformÃ¡tica', 1, 'grado'),
('IngenierÃ­a Civil', 1, 'grado'),
('MBA', 2, 'posgrado'),
('EspecializaciÃ³n en Derecho Civil', 3, 'posgrado');

INSERT INTO participante (ci, nombre, apellido, email) VALUES
('12345678', 'Santiago', 'Pellejero', 'spellejero@ucu.edu.uy'),
('98765432', 'MarÃ­a', 'RodrÃ­guez', 'mrodriguez@ucu.edu.uy'),
('11112222', 'Carlos', 'GonzÃ¡lez', 'cgonzalez@ucu.edu.uy'),
('22223333', 'LucÃ­a', 'FernÃ¡ndez', 'lfernandez@ucu.edu.uy');

INSERT INTO login (email, password, role) VALUES
('spellejero@ucu.edu.uy', 'hash_pwd_sample_1', 'admin'),
('mrodriguez@ucu.edu.uy', 'hash_pwd_sample_2', 'alumno');

INSERT INTO participante_programa_academico (ci_participante, id_programa, rol) VALUES
('12345678', 1, 'alumno'),
('98765432', 3, 'alumno'),
('11112222', 1, 'docente'),
('22223333', 4, 'alumno');

INSERT INTO edificio (nombre_edificio, direccion, departamento) VALUES
('Edificio Central', 'Av. 8 de Octubre 2738', 'Montevideo'),
('Biblioteca Norte', 'Bvar. EspaÃ±a 1234', 'Montevideo');

INSERT INTO sala (nombre_sala, id_edificio, capacidad, tipo_sala) VALUES
('Sala A1', 1, 6, 'libre'),
('Sala A2', 1, 4, 'libre'),
('Sala Posgrado 1', 2, 8, 'posgrado'),
('Sala Docentes 1', 1, 4, 'docente');

INSERT INTO turno (hora_inicio, hora_fin) VALUES
('08:00:00','09:00:00'),
('09:00:00','10:00:00'),
('10:00:00','11:00:00'),
('11:00:00','12:00:00'),
('12:00:00','13:00:00'),
('13:00:00','14:00:00'),
('14:00:00','15:00:00'),
('15:00:00','16:00:00'),
('16:00:00','17:00:00'),
('17:00:00','18:00:00'),
('18:00:00','19:00:00'),
('19:00:00','20:00:00'),
('20:00:00','21:00:00'),
('21:00:00','22:00:00'),
('22:00:00','23:00:00');

-- TRIGGERS: Validaciones y sanciones automÃ¡ticas (resumen)
DELIMITER 
CREATE TRIGGER trg_before_insert_reserva_participante
BEFORE INSERT ON reserva_participante
FOR EACH ROW
BEGIN
    DECLARE v_capacidad INT DEFAULT 0;
    DECLARE v_cont INT DEFAULT 0;
    DECLARE v_fecha DATE;
    DECLARE v_is_docente INT DEFAULT 0;
    DECLARE v_is_posgrado INT DEFAULT 0;
    DECLARE v_sala_tipo ENUM('libre','posgrado','docente');
    DECLARE v_week_count INT DEFAULT 0;

    SELECT r.fecha, s.capacidad, s.tipo_sala
    INTO v_fecha, v_capacidad, v_sala_tipo
    FROM reserva r
    JOIN sala s ON r.id_sala = s.id_sala
    WHERE r.id_reserva = NEW.id_reserva
    LIMIT 1;

    IF v_fecha IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Reserva inexistente';
    END IF;

    SELECT COUNT(*) INTO v_cont FROM reserva_participante WHERE id_reserva = NEW.id_reserva;
    IF v_cont + 1 > v_capacidad THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Capacidad de la sala excedida';
    END IF;

    SELECT COUNT(*) INTO v_is_docente
    FROM participante_programa_academico
    WHERE ci_participante = NEW.ci_participante AND rol = 'docente';

    SELECT COUNT(*) INTO v_is_posgrado
    FROM participante_programa_academico ppa
    JOIN programa_academico pa ON ppa.id_programa = pa.id_programa
    WHERE ppa.ci_participante = NEW.ci_participante AND pa.tipo = 'posgrado';

    IF v_sala_tipo = 'docente' AND v_is_docente = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo docentes pueden reservar salas de tipo docente';
    END IF;

    IF v_sala_tipo = 'posgrado' AND (v_is_docente = 0 AND v_is_posgrado = 0) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo docentes o estudiantes de posgrado pueden reservar salas de posgrado';
    END IF;

    IF v_is_docente = 0 AND v_is_posgrado = 0 THEN
        SELECT COUNT(*) INTO v_cont
        FROM reserva_participante rp
        JOIN reserva r ON rp.id_reserva = r.id_reserva
        WHERE rp.ci_participante = NEW.ci_participante
          AND r.fecha = v_fecha
          AND r.estado = 'activa';

        IF v_cont >= 2 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'LÃ­mite diario (2 horas) excedido para este participante';
        END IF;

        SELECT COUNT(*) INTO v_week_count
        FROM reserva_participante rp
        JOIN reserva r ON rp.id_reserva = r.id_reserva
        WHERE rp.ci_participante = NEW.ci_participante
          AND YEARWEEK(r.fecha, 1) = YEARWEEK(v_fecha,1)
          AND r.estado = 'activa';

        IF v_week_count >= 3 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'LÃ­mite semanal (3 reservas activas) excedido para este participante';
        END IF;
    END IF;
END

CREATE TRIGGER trg_after_update_reserva_estado
AFTER UPDATE ON reserva
FOR EACH ROW
BEGIN
    IF NEW.estado = 'sin_asistencia' AND OLD.estado <> 'sin_asistencia' THEN
        INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin, motivo)
        SELECT rp.ci_participante, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 2 MONTH),
               CONCAT('No asistencia a reserva ', NEW.id_reserva)
        FROM reserva_participante rp
        WHERE rp.id_reserva = NEW.id_reserva;

        INSERT INTO notificacion (ci_participante, tipo, asunto, cuerpo, destinatario_email, estado, next_intento_at)
        SELECT rp.ci_participante, 'sancion',
               CONCAT('SanciÃ³n por no asistencia - Reserva ', NEW.id_reserva),
               CONCAT('Se le ha generado una sanciÃ³n por no asistencia a la reserva ', NEW.id_reserva,
                      '. Fecha inicio: ', DATE_FORMAT(CURDATE(), '%Y-%m-%d'),
                      '. Fecha fin: ', DATE_FORMAT(DATE_ADD(CURDATE(), INTERVAL 2 MONTH), '%Y-%m-%d')),
               p.email, 'pendiente', NOW()
        FROM reserva_participante rp
        JOIN participante p ON p.ci = rp.ci_participante
        WHERE rp.id_reserva = NEW.id_reserva;
    END IF;
END

DELIMITER ;

-- PROCEDURE para marcar no-shows y EVENT (requiere event_scheduler ON)
DELIMITER 
CREATE PROCEDURE marcar_reservas_sin_asistencia()
BEGIN
  UPDATE reserva r
  JOIN turno t ON r.id_turno = t.id_turno
  SET r.estado = 'sin_asistencia'
  WHERE r.estado = 'activa'
    AND STR_TO_DATE(CONCAT(r.fecha, ' ', t.hora_fin), '%Y-%m-%d %H:%i:%s') <= NOW()
    AND NOT EXISTS (
      SELECT 1 FROM reserva_participante rp WHERE rp.id_reserva = r.id_reserva AND rp.asistencia = TRUE
    );
END

CREATE EVENT IF NOT EXISTS ev_marcar_sin_asistencia
ON SCHEDULE EVERY 5 MINUTE
DO
BEGIN
  CALL marcar_reservas_sin_asistencia();
END
DELIMITER ;

-- SP para sanciones
DELIMITER 
CREATE PROCEDURE sp_create_sancion (
  IN p_ci VARCHAR(15),
  IN p_fecha_inicio DATE,
  IN p_fecha_fin DATE,
  IN p_motivo VARCHAR(200)
)
BEGIN
  INSERT INTO sancion_participante (ci_participante, fecha_inicio, fecha_fin, motivo)
  VALUES (p_ci, p_fecha_inicio, p_fecha_fin, p_motivo);
END
DELIMITER ;

CREATE INDEX idx_reserva_fecha ON reserva(fecha);
CREATE INDEX idx_rp_ci ON reserva_participante(ci_participante);
CREATE INDEX idx_sala_edificio ON sala(id_edificio);
