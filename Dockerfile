FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dashboard dashboard
COPY tinyml/models/weights.npz tinyml/models/weights.npz
RUN useradd --create-home classroom && mkdir runtime && chown classroom runtime
USER classroom
ENV PUBLIC_DEPLOYMENT=1 SIMULATOR_ENABLED=1
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8000"]
