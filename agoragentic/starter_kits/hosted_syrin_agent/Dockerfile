FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r agoragentic/starter_kits/hosted_syrin_agent/requirements.txt

EXPOSE 8000

CMD ["python", "agoragentic/starter_kits/hosted_syrin_agent/serve.py"]
