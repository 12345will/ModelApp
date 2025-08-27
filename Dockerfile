# Dockerfile
FROM python:3.10-slim

# Prevents Python from writing .pyc files & output buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bind to 0.0.0.0 and respect a provided PORT (App Service sets WEBSITES_PORT internally)
# Fall back to 8501 locally.
ENV PORT=8501
CMD ["bash", "-lc", "streamlit run model.py --server.address=0.0.0.0 --server.port=${PORT}"]
