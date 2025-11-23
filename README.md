# Sistema de Gestión de Reservas de Salas de Estudio

Sistema completo para la gestión de reservas de salas de estudio en una universidad, desarrollado en Python + MySQL sin uso de ORM, con interfaz web Flask y aplicación de consola.

## 📋 Características

### 🌐 **Aplicación Web (Flask)**
- **Registro e Inicio de Sesión**: Sistema completo de autenticación con bcrypt
- **Panel de Usuario (Estudiantes)**:
  - Ver salas disponibles con capacidad y tipo
  - Crear reservas con validación automática de reglas
  - Ver historial de reservas
  - Cancelar reservas activas
  - Alertas de sanciones activas
- **Panel de Administrador (Docentes)**:
  - Dashboard con estadísticas en tiempo real
  - Gestión completa de participantes
  - Administración de salas
  - Control de todas las reservas
  - Gestión de sanciones
  - Reportes con gráficos interactivos (Chart.js)
- **Seguridad**:
  - Contraseñas hasheadas con bcrypt
  - Separación de roles (Usuario/Administrador)
  - Protección de rutas con decoradores
  - Prevención de SQL injection con queries parametrizadas

### 🖥️ **Aplicación de Consola (Python)**
- Menú interactivo para gestión completa
- Módulos ABM (Alta, Baja, Modificación)
- Sistema de reportes SQL

### 🎓 **Sistema de Roles**
- **Alumno de Grado**: Acceso a salas libres, límites de 2h/día y 3 reservas/semana
- **Alumno de Posgrado**: Acceso a salas libres y de posgrado, sin límites en salas exclusivas
- **Docente**: Acceso completo (admin), puede usar todas las salas sin restricciones

## 🔧 Requisitos

### Localmente
- Python 3.8 o superior
- MySQL 8.0 o superior
- pip (gestor de paquetes de Python)

### Con Docker
- Docker
- Docker Compose

## 🚀 Instalación y Ejecución

### Opción 1: Ejecución con Docker (Recomendada)

#### 1. **Clonar o descargar el proyecto**

#### 2. **Iniciar con Docker**

```bash
# Construir e iniciar servicios
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Esperar a ver: "MySQL está listo!" y "Running on http://0.0.0.0:5000"
```

#### 3. **Acceder a la aplicación**

- **Aplicación Web**: http://localhost:5000
- **Aplicación Consola**: 
  ```bash
  docker exec -it reservas_app python main.py
  ```

#### 4. **Detener servicios**

```bash
docker-compose down
```

### Opción 2: Ejecución Local (Sin Docker)

#### 1. **Instalar MySQL** (si no lo tiene)
Descargar desde: https://dev.mysql.com/downloads/mysql/

#### 2. **Crear la base de datos**

```bash
mysql -u root -p < sql/create_db.sql
mysql -u root -p reservas_salas < sql/insert_data.sql
```

#### 3. **Configurar conexión**

Editar `db/connection.py` si es necesario:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'tu_password',  # Cambiar
    'database': 'reservas_salas',
    'charset': 'utf8mb4'
}
```

#### 4. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

#### 5. **Ejecutar la aplicación**

```bash
# Aplicación Web
python app.py
# Acceder en: http://localhost:5000

# O Aplicación de Consola
python main.py
```

## 📊 Estructura del Proyecto (Versión Modular)

```
reservas_salas/
│
├── db/
│   ├── __init__.py              # Inicialización paquete db
│   └── connection.py            # Conexión y operaciones MySQL
│
├── modules/
│   ├── __init__.py              # Inicialización paquete modules
│   ├── participantes.py         # Gestión de participantes
│   ├── salas.py                 # Gestión de salas
│   ├── reservas.py              # Gestión de reservas
│   ├── sanciones.py             # Gestión de sanciones
│   ├── validations.py           # Validaciones de reglas de negocio
│   └── reportes.py              # Reportes y consultas SQL
│
├── sql/
│   ├── create_db.sql            # Script de creación de base de datos
│   └── insert_data.sql          # Datos de ejemplo
│
├── main.py                       # Aplicación principal (punto de entrada)
├── requirements.txt              # Dependencias Python
├── Dockerfile                    # Imagen Docker
├── docker-compose.yml            # Orquestación Docker
├── .dockerignore                 # Archivos a ignorar en Docker
├── .gitignore                    # Archivos a ignorar en Git
└── README.md                     # Documentación completa
```

### Ventajas de la Estructura Modular

- ✅ **Separación de responsabilidades**: Cada módulo tiene una función específica
- ✅ **Mantenibilidad**: Fácil localizar y modificar funcionalidades
- ✅ **Reutilización**: Funciones compartidas entre módulos
- ✅ **Escalabilidad**: Agregar nuevos módulos sin afectar existentes
- ✅ **Testeable**: Cada módulo puede probarse independientemente

## 🗃️ Esquema de Base de Datos

### Tablas Principales
- **login**: Credenciales de acceso
- **participante**: Datos de usuarios
- **programa_academico**: Carreras y programas
- **participante_programa_academico**: Relación participante-programa
- **facultad**: Facultades de la universidad
- **sala**: Salas disponibles para reserva
- **edificio**: Edificios de la universidad
- **turno**: Bloques horarios (8:00-23:00)
- **reserva**: Reservas realizadas
- **reserva_participante**: Participantes en cada reserva
- **sancion_participante**: Sanciones aplicadas

## 📖 Reglas de Negocio

1. ✅ Las salas se reservan por bloques de 1 hora (8:00 - 23:00)
2. ✅ Máximo 2 horas por día por participante (salvo privilegiados)
3. ✅ Máximo 3 reservas activas por semana (salvo privilegiados)
4. ✅ Docentes y estudiantes de posgrado pueden usar salas exclusivas
5. ✅ No se puede exceder la capacidad de la sala
6. ✅ Si nadie asiste, todos los participantes son sancionados 2 meses
7. ✅ Validación en todas las capas (BD, backend)

## 📊 Reportes Disponibles

1. **Salas más reservadas**: Top 10 salas con más demanda
2. **Turnos más demandados**: Horarios más solicitados
3. **Promedio de participantes**: Por cada sala
4. **Reservas por carrera**: Agrupado por facultad y programa
5. **Ocupación por edificio**: Porcentaje últimos 30 días
6. **Reservas por tipo de usuario**: Docentes, grado, posgrado
7. **Sanciones por tipo de usuario**: Análisis de comportamiento
8. **Efectividad de reservas**: Activas vs canceladas vs sin asistencia
9. **Horas por semana**: Total de horas reservadas últimas 8 semanas
10. **Participantes más sancionados**: Top 10 usuarios
11. **Edificios con más cancelaciones**: Análisis por ubicación

## 🎯 Módulos Funcionales

### 1. Gestión de Participantes
- Listar todos los participantes con sus programas
- Crear nuevos participantes (con hash de contraseña bcrypt)
- Modificar datos de participantes
- Eliminar participantes

### 2. Gestión de Salas
- Listar salas con capacidad y tipo
- Crear nuevas salas
- Modificar capacidad y tipo de sala
- Eliminar salas

### 3. Gestión de Reservas
- Listar reservas con estado y participantes
- Crear reservas (con validación completa)
- Cancelar reservas
- Registrar asistencia (con aplicación automática de sanciones)

### 4. Gestión de Sanciones
- Listar sanciones activas y pasadas
- Crear sanciones manuales
- Eliminar sanciones

### 5. Reportes
- 11 reportes SQL para análisis de datos

## 🔐 Seguridad

- Contraseñas hasheadas con **bcrypt**
- Validaciones en múltiples capas
- Uso de parámetros preparados para prevenir SQL injection
- Transacciones para operaciones críticas

## 💡 Datos de Ejemplo

El sistema incluye datos de ejemplo:
- 8 participantes (4 alumnos, 2 docentes, 2 posgrado)
- 4 facultades
- 7 programas académicos
- 3 edificios
- 9 salas (libres, posgrado, docentes)
- 15 turnos (8:00 a 23:00)
- 6 reservas iniciales

## 🛠️ Tecnologías Utilizadas

- **Python 3.11**: Lenguaje de programación
- **MySQL 8.0**: Base de datos relacional
- **mysql-connector-python**: Conector MySQL para Python
- **bcrypt**: Hashing de contraseñas
- **Docker**: Contenedorización (opcional)

## 📝 Notas Importantes

- El sistema **NO** usa ORM, todas las consultas son SQL nativo
- Las validaciones están implementadas en todas las capas
- Se incluye manejo de errores y mensajes claros
- El código está comentado y es fácil de leer
- Funciones reutilizables para operaciones comunes

## ⚙️ Configuración Avanzada

### Cambiar puerto de MySQL en Docker
Editar `docker-compose.yml`:
```yaml
ports:
  - "3307:3306"  # Puerto externo:interno
```

### Agregar más turnos
```sql
INSERT INTO turno (hora_inicio, hora_fin) VALUES ('23:00:00', '24:00:00');
```

### Crear nuevos edificios
```sql
INSERT INTO edificio (nombre_edificio, direccion, departamento) 
VALUES ('Edificio Oeste', 'Calle Oeste 123', 'Montevideo');
```

## 🐛 Solución de Problemas

### Error de conexión a MySQL
- Verificar que MySQL esté ejecutándose
- Verificar usuario y contraseña en `DB_CONFIG`
- Verificar que la base de datos existe

### Error de permisos
- Asegurar que el usuario MySQL tenga permisos
- Ejecutar: `GRANT ALL PRIVILEGES ON reservas_salas.* TO 'root'@'localhost';`

### Error de módulos Python
- Reinstalar dependencias: `pip install -r requirements.txt`
- Verificar versión de Python: `python --version`

## 📧 Soporte

Para consultas o problemas, revisar:
1. Los mensajes de error en consola
2. Los logs de MySQL
3. La configuración de conexión

## 📄 Licencia

Este proyecto es de código abierto para fines educativos.

---

**Desarrollado para**: Sistema de Gestión Universitaria  
**Versión**: 1.0  
**Fecha**: 2025