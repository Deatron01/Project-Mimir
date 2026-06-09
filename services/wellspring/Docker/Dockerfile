# Alapkép kiválasztása (könnyűsúlyú Python 3.11)
FROM python:3.11-slim

# Munkakönyvtár beállítása a konténeren belül
WORKDIR /app

# Rendszer szintű függőségek és a Tesseract OCR (magyar/angol nyelvvel) telepítése
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-hun \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Csak a requirements.txt másolása először (a gyorsabb Docker cache miatt)
COPY Docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# A teljes forráskód átmásolása a munkakönyvtárba
COPY . .

# Indítási parancs
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]