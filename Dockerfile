#base environment
FROM python:3.11-slim

# Evita .pyc y fuerza logs inmediatos
#runtime configuration
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependencias
# dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY app/ .

# Puerto de Flask
EXPOSE 5000

# Arranque de la app
CMD ["python", "app.py"]



