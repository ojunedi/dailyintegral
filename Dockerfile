FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY migrations/ migrations/
COPY integrals.db .
COPY run.py .
COPY gunicorn.conf.py .

RUN python -m migrations.migrate

ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

CMD ["gunicorn", "run:app", "-c", "gunicorn.conf.py"]
