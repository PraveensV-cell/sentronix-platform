FROM python:3.11-slim


WORKDIR /app


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app


COPY services/event-service/requirements.txt .


RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


COPY libs/ /libs/

RUN pip install -e /libs/shared


COPY services/event-service/ /app/


EXPOSE 8004


CMD ["uvicorn","src.main:app","--host","0.0.0.0","--port","8004"]
