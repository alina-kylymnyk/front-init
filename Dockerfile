
FROM python:3.10-slim


ENV APP_HOME=/app


WORKDIR $APP_HOME


COPY pyproject.toml poetry.lock* ./


RUN pip install poetry

RUN poetry config virtualenvs.create false && poetry install --only main


COPY . .


EXPOSE 8080


CMD ["python", "app.py"]
