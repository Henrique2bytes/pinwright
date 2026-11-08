FROM python:3.12-slim

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app
WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests ./tests
COPY examples ./examples
COPY demos ./demos

RUN pip install --no-cache-dir . \
    && chown -R app:app /app

USER app
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
