# Intentionally vulnerable lab target — DO NOT use in production
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.3 requests==2.32.3
COPY app.py .
EXPOSE 5055
CMD ["python", "app.py"]
