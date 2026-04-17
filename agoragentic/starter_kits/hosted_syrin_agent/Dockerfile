FROM python:3.11.15-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY . /app

RUN pip install --no-cache-dir -r agoragentic/starter_kits/hosted_syrin_agent/requirements.txt \
    && chown -R appuser:appuser /app

# EXPOSE documents the default port only; set HOSTED_SYRIN_PORT at runtime to change it.
EXPOSE 8000

USER appuser
CMD ["python", "agoragentic/starter_kits/hosted_syrin_agent/serve.py"]
