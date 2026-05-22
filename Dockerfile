FROM python:3.11-slim

# System dependencies for OpenCV and font rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Font and background directories (override via -v or ENV)
ENV FONT_DIRS=/app/fonts
ENV BG_DIR=/app/backgrounds

RUN mkdir -p /app/fonts /app/backgrounds

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
