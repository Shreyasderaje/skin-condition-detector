# Backend image (core stack, demo/real inference via Python).
# To bake in the full ML stack, swap the requirements file for
# backend/requirements-ml.txt (+~2GB for torch) and copy model.pth into ml/.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
