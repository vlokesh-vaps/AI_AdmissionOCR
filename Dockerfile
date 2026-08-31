FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5007

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

COPY app ./app

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 5007

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5007"]
