# Sistema de Gestión de Reservas de Salas de Estudio

Sistema completo de gestión de reservas de salas universitarias desarrollado en Python + Flask + MySQL, con ABM completo, reportes BI y arquitectura modular sin uso de ORM.

## 🌟 Características Principales

### 🌐 **Aplicación Web (Flask)**

#### **Panel de Usuario (Estudiantes/Docentes)**
- ✅ **Registro e Inicio de Sesión**: Autenticación segura con bcrypt
- ✅ **Gestión de Reservas**:
  - Crear reservas con validación automática de reglas de negocio
  - Ver historial completo de reservas
  - Cancelar reservas activas
  - Sistema de alertas para sanciones
- ✅ **Exploración de Salas**:
  - Visualización de salas por edificio
  - Información de capacidad y tipo
  - Disponibilidad en tiempo real
- ✅ **Gestión de Perfil**:
  - Cambiar contraseña con validación de seguridad
  - Ver programas académicos asociados

#### **Panel de Administrador (Docentes)**
- ✅ **Dashboard Ejecutivo**:
  - Estadísticas en tiempo real
  - Gráficos de uso del sistema
  - Métricas de rendimiento
  
- ✅ **ABM Completo de Participantes**:
  - Alta: Registro con hash bcrypt
  - Baja: Eliminación con validación de dependencias
  - Modificación: Actualización de datos personales
  - Gestión de programas académicos por participante
  
- ✅ **ABM Completo de Salas**:
  - Alta: Creación de salas con tipos específicos
  - Baja: Eliminación validando reservas activas
  - Modificación: Edición de capacidad y tipo
  - Gestión de edificios
  - Estadísticas de uso por sala
  
- ✅ **ABM Completo de Reservas**:
  - Alta: Creación manual de reservas
  - Baja: Eliminación de reservas canceladas
  - Modificación: Cambio de fecha, horario y sala
  - Gestión de participantes en reservas
  - Registro de asistencia individual
  - Cambio de estado (activa/cancelada/finalizada)
  
- ✅ **ABM Completo de Sanciones**:
  - Alta: Creación con duraciones predefinidas (7, 15, 30, 60 días)
  - Baja: Eliminación manual
  - Modificación: Ajuste de fechas
  - Finalización anticipada
  - Estadísticas de sanciones
  
- ✅ **Sistema de Reportes BI**:
  - 11 reportes con visualizaciones (Chart.js)
  - Gráficos interactivos (barras, líneas, tortas)
  - Exportación de datos
  - Consultas SQL dinámicas desde archivo

### 🖥️ **Aplicación de Consola (Python CLI)**
- Menú interactivo completo
- Todas las operaciones ABM disponibles
- Sistema de reportes integrado

### 🎓 **Sistema de Roles y Permisos**

| Rol | Acceso Salas | Límites | Privilegios Admin |
|-----|--------------|---------|-------------------|
| **Alumno Grado** | Libre, Salón | 2h/día, 3 reservas/semana | ❌ |
| **Alumno Posgrado** | Libre, Salón, Laboratorio | Sin límites en exclusivas | ❌ |
| **Docente** | Todas (incluyendo Auditorios) | Sin límites | ✅ Panel Admin |

## 🏗️ Arquitectura del Sistema

### Estructura Modular

```
reservas_salas/
│
├── app.py                        # Aplicación Flask principal (ABM + Reportes)
├── main.py                       # Aplicación CLI (consola)
│
├── db/
│   ├── __init__.py
│   └── connection.py             # Pool de conexiones MySQL
│
├── modules/                      # Módulos de negocio
│   ├── __init__.py
│   ├── participantes.py          # ABM Participantes
│   ├── salas.py                  # ABM Salas
│   ├── reservas.py               # ABM Reservas
│   ├── sanciones.py              # ABM Sanciones
│   ├── validations.py            # Reglas de negocio
│   └── reportes.py               # Consultas BI
│
├── templates/                    # Vistas HTML
│   ├── base.html                 # Template base
│   ├── index.html                # Landing page
│   ├── login.html                # Inicio de sesión
│   ├── register.html             # Registro
│   │
│   ├── user/                     # Vistas de usuario
│   │   ├── dashboard.html
│   │   ├── salas.html
│   │   ├── reservar.html
│   │   └── cambiar_password.html
│   │
│   └── admin/                    # Vistas de administrador
│       ├── dashboard.html
│       ├── participantes.html
│       ├── editar_participante.html
│       ├── salas.html
│       ├── crear_sala.html
│       ├── editar_sala.html
│       ├── crear_edificio.html
│       ├── reservas.html
│       ├── editar_reserva.html
│       ├── gestionar_participantes_reserva.html
│       ├── sanciones.html
│       ├── crear_sancion.html
│       ├── editar_sancion.html
│       └── reportes.html
│
├── sql/
│   ├── create_db.sql             # DDL completo
│   ├── insert_data.sql           # Datos de ejemplo
│   └── consultas_reportes.sql    # Queries BI
│
├── requirements.txt              # Dependencias Python
├── Dockerfile                    # Imagen Docker
├── docker-compose.yml            # Orquestación
└── README.md                     # Este archivo
```

## 🔧 Tecnologías Utilizadas

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Backend | Python | 3.11+ |
| Framework Web | Flask | 3.0+ |
| Base de Datos | MySQL | 8.0+ |
| Conector DB | mysql-connector-python | 8.3+ |
| Seguridad | bcrypt | 4.1+ |
| Frontend | Bootstrap | 5.3 |
| Gráficos | Chart.js | 4.4 |
| Iconos | Bootstrap Icons | 1.11 |
| Contenedores | Docker + Docker Compose | 24.0+ |

## 🚀 Instalación

### Opción 1: Docker (Recomendada) 🐳

```bash
# 1. Clonar repositorio
git clone <url-repositorio>
cd reservas_salas

# 2. Iniciar servicios
docker-compose up -d --build

# 3. Verificar logs
docker-compose logs -f

# 4. Acceder
# Web: http://localhost:5000
# CLI: docker exec -it reservas_app python main.py

# 5. Detener
docker-compose down
```

### Opción 2: Instalación Local 💻

#### Requisitos
- Python 3.11+
- MySQL 8.0+
- pip

#### Pasos

```bash
# 1. Crear base de datos
mysql -u root -p < sql/create_db.sql
mysql -u root -p reserva_salas < sql/insert_data.sql

# 2. Configurar conexión (db/connection.py)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'tu_password',
    'database': 'reserva_salas'
}

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar aplicación
python app.py
# o
python main.py
```

## 📊 Modelo de Datos

### Entidades Principales

```
PARTICIPANTE (usuario del sistema)
    └── N:M PROGRAMA_ACADEMICO (con rol)
            └── N:1 FACULTAD

RESERVA (bloque de tiempo reservado)
    ├── N:1 SALA
    │   └── N:1 EDIFICIO
    ├── N:1 TURNO (bloque horario)
    └── N:M PARTICIPANTE (asistencia)

SANCION (restricción temporal)
    └── N:1 PARTICIPANTE
```

### Tipos de Salas

| Tipo | Usuarios Permitidos | Uso |
|------|---------------------|-----|
| **Libre** | Todos | Estudio general |
| **Salón** | Alumnos de Grado | Clases |
| **Laboratorio** | Alumnos de Posgrado | Investigación |
| **Auditorio** | Docentes | Eventos |

## 📋 Reglas de Negocio

### Restricciones Generales
1. ✅ Bloques horarios de 1 hora (8:00 - 23:00)
2. ✅ No exceder capacidad de sala
3. ✅ No solapar reservas en misma sala/turno
4. ✅ Validación de compatibilidad sala-usuario

### Restricciones por Rol

#### Alumnos de Grado
- Máximo **2 horas/día**
- Máximo **3 reservas activas/semana**
- Solo salas **libres** y **salones**

#### Alumnos de Posgrado
- Sin límites en salas exclusivas
- Acceso a **laboratorios**

#### Docentes
- Sin restricciones
- Acceso a **auditorios**
- Panel administrativo completo

### Sistema de Sanciones
- ⚠️ **Inasistencia total**: 2 meses de sanción automática
- 🚫 **Durante sanción**: No se pueden crear reservas
- ✅ **Reservas existentes**: No se cancelan automáticamente

## 📈 Reportes Disponibles

| # | Reporte | Descripción | Visualización |
|---|---------|-------------|---------------|
| 1 | Salas Más Reservadas | Top 10 con más demanda | Gráfico de barras |
| 2 | Turnos Demandados | Horarios más solicitados | Gráfico de líneas |
| 3 | Promedio Participantes | Por sala | Gráfico de barras |
| 4 | Reservas por Carrera | Agrupado por facultad | Tabla |
| 5 | Ocupación por Edificio | % últimos 30 días | Gráfico de barras |
| 6 | Reservas por Tipo Usuario | Docentes vs alumnos | Tabla |
| 7 | Sanciones por Tipo | Análisis disciplinario | Gráfico circular |
| 8 | Efectividad de Reservas | Activas vs canceladas | Gráfico circular |
| 9 | Horas por Semana | Últimas 8 semanas | Gráfico de líneas |
| 10 | Participantes Sancionados | Top 10 | Tabla |
| 11 | Edificios con Cancelaciones | Por ubicación | Tabla |

## 🔐 Seguridad

### Implementaciones
- ✅ **Hashing**: bcrypt con salt automático
- ✅ **SQL Injection**: Queries parametrizadas
- ✅ **Autenticación**: Sistema de sesiones Flask
- ✅ **Autorización**: Decoradores `@login_required` y `@admin_required`
- ✅ **Validación**: Múltiples capas (BD, backend, frontend)
- ✅ **Transacciones**: Operaciones atómicas con rollback

### Ejemplo de Hash
```python
# Al crear usuario
hash_pass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Al verificar login
bcrypt.checkpw(password.encode('utf-8'), hash_almacenado)
```

## 💾 Datos de Ejemplo

El sistema incluye:
- 👥 **8 participantes** (roles variados)
- 🏫 **4 facultades**
- 📚 **7 programas académicos**
- 🏢 **3 edificios**
- 🚪 **9 salas** (tipos variados)
- ⏰ **15 turnos** (8:00-23:00)
- 📅 **6 reservas iniciales**

### Usuarios de Prueba

| Email | Contraseña | Rol | Acceso |
|-------|------------|-----|--------|
| `juan.perez@universidad.edu` | `password123` | Alumno Grado | Usuario |
| `maria.garcia@universidad.edu` | `password123` | Docente | Administrador |
| `carlos.rodriguez@universidad.edu` | `password123` | Alumno Posgrado | Usuario |

## 🎯 Casos de Uso Principales

### Para Usuarios
1. **Reservar Sala**:
   - Login → Reservar → Seleccionar sala/fecha/turno → Confirmar
   - Validaciones automáticas aplicadas
   
2. **Cancelar Reserva**:
   - Dashboard → Mis Reservas → Cancelar
   - Solo reservas activas

3. **Ver Historial**:
   - Dashboard → Tabla de reservas con estados

### Para Administradores
1. **Gestionar Participantes**:
   - Admin → Participantes → Crear/Editar/Eliminar
   - Asignar programas y roles
   
2. **Gestionar Reservas**:
   - Admin → Reservas → Ver detalles
   - Cambiar estado, agregar/quitar participantes
   - Registrar asistencia

3. **Aplicar Sanciones**:
   - Admin → Sanciones → Crear
   - Seleccionar duración predefinida o custom
   - Finalizar anticipadamente si corresponde

4. **Ver Reportes**:
   - Admin → Reportes → Seleccionar tipo
   - Visualización gráfica interactiva

## 🐛 Solución de Problemas

### Error: "Conexión rechazada MySQL"
```bash
# Verificar estado
docker-compose ps
# o
systemctl status mysql

# Verificar puerto
netstat -tuln | grep 3306
```

### Error: "Módulo no encontrado"
```bash
pip install -r requirements.txt --force-reinstall
```

### Error: "Tabla no existe"
```bash
# Recrear base de datos
docker-compose down -v
docker-compose up -d
```

### Error: "Permission denied"
```bash
# Dar permisos a MySQL
GRANT ALL PRIVILEGES ON reserva_salas.* TO 'root'@'%';
FLUSH PRIVILEGES;
```

## 📚 Documentación Adicional

- [Informe Técnico](INFORME.md) - Decisiones de implementación
- [API Reference](docs/API.md) - Endpoints disponibles
- [Guía de Desarrollo](docs/DESARROLLO.md) - Para contribuidores

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto es de código abierto para fines educativos.

## 👥 Autores

- **Equipo de Desarrollo** - Sistema de Gestión Universitaria

## 📧 Contacto

Para consultas: repositorio@universidad.edu

---

**Versión**: 2.0.0  
**Última actualización**: Enero 2025  
**Estado**: Producción ✅