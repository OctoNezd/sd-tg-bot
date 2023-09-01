FROM python:3-bookworm
ENV POETRY_HOME=/opt/poetry
ENV PATH=${POETRY_HOME}/bin:$PATH
RUN useradd -ms /bin/bash bot
WORKDIR /home/bot
RUN curl -sSL https://install.python-poetry.org | python3 -
COPY pyproject.toml poetry.lock /home/bot/
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-dev
USER bot
COPY *.py .
CMD ["python3", "main.py"]
