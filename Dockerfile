FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    default-mysql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de requisitos primero
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de archivos
COPY . .

# Exponer puerto 5000 para Flask
EXPOSE 5000

# Comando por defecto
CMD ["python", "app.py"]