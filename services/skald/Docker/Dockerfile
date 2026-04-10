# Alapkép kiválasztása (könnyűsúlyú Python 3.11)
FROM python:3.11-slim

# Munkakönyvtár beállítása a konténeren belül
WORKDIR /app

# Rendszer szintű függőségek telepítése (ha kell pl. a PDF feldolgozáshoz)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Csak a requirements.txt másolása először (a gyorsabb Docker cache miatt)
COPY Docker/requirements.txt .

# Csomagok telepítése venv NÉLKÜL, közvetlenül a konténerbe
RUN pip install --no-cache-dir -r requirements.txt

# A teljes forráskód átmásolása a munkakönyvtárba (kivéve, ami a .dockerignore-ban van)
COPY . .

# Indítási parancs (Példa FastAPI-hoz)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]