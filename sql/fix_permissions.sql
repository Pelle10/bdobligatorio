-- Script para corregir permisos de usuario en MySQL

-- Otorgar todos los permisos al usuario root
GRANT ALL PRIVILEGES ON reservas_salas.* TO 'root'@'%' IDENTIFIED BY 'root';
GRANT ALL PRIVILEGES ON reservas_salas.* TO 'root'@'localhost' IDENTIFIED BY 'root';

-- Aplicar cambios
FLUSH PRIVILEGES;

-- Verificar
SHOW GRANTS FOR 'root'@'%';