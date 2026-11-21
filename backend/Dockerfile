FROM python:3.12-slim
WORKDIR /app
ARG WITH_ML=false
COPY requirements.txt requirements-postgres.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-postgres.txt "psycopg[binary]" \
 && if [ "$WITH_ML" = "true" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
ENV PYTHONPATH=/app
ENV AUTO_CREATE_TABLES=true
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000"]