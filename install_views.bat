@echo off
REM Script para instalar las vistas de reportes en MySQL (Windows)

echo ======================================================
echo 📊 INSTALACIÓN DE VISTAS PARA REPORTES BI
echo ======================================================
echo.

REM Verificar si Docker está corriendo
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker no está corriendo o no está instalado
    echo Por favor inicia Docker Desktop
    pause
    exit /b 1
)

REM Verificar si el contenedor de MySQL existe
docker ps | findstr reservas_mysql >nul
if %errorlevel% equ 0 (
    echo ✅ Detectado MySQL en Docker
    echo Instalando vistas...
    echo.
    
    docker exec -i reservas_mysql mysql -uroot -proot reservas_salas < sql\views_reportes.sql
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ Vistas instaladas exitosamente!
        echo.
        echo Verificando vistas creadas:
        echo.
        docker exec -i reservas_mysql mysql -uroot -proot -e "SELECT TABLE_NAME as Vista FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'reservas_salas' AND TABLE_TYPE = 'VIEW' ORDER BY TABLE_NAME;"
    ) else (
        echo.
        echo ❌ Error al instalar vistas
        pause
        exit /b 1
    )
) else (
    echo ❌ Contenedor reservas_mysql no encontrado
    echo Por favor ejecuta: docker-compose up -d
    pause
    exit /b 1
)

echo.
echo ======================================================
echo ✅ INSTALACIÓN COMPLETADA
echo ======================================================
echo.
echo Las 11 vistas están ahora disponibles:
echo   1. v_salas_mas_reservadas
echo   2. v_turnos_mas_demandados
echo   3. v_promedio_participantes_sala
echo   4. v_reservas_por_carrera_facultad
echo   5. v_ocupacion_por_edificio
echo   6. v_reservas_asistencias_por_tipo
echo   7. v_sanciones_por_tipo_usuario
echo   8. v_efectividad_reservas
echo   9. v_horas_reservadas_por_semana
echo  10. v_participantes_mas_sancionados
echo  11. v_edificios_mas_cancelaciones
echo.
echo Para probar una vista:
echo   docker exec -i reservas_mysql mysql -uroot -proot -e "SELECT * FROM reservas_salas.v_salas_mas_reservadas LIMIT 5;"
echo.
pause