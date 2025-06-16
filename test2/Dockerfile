# syntax=docker/dockerfile:1

FROM python:3.13-slim

WORKDIR /app

COPY . .

COPY BaltimoreCyberTrustRoot.crt.pem /app/BaltimoreCyberTrustRoot.crt.pem

RUN apt-get update && apt-get install -y bash
RUN pip3 install --no-cache-dir -r requirements.txt
RUN chmod +x ./start.sh

EXPOSE 5000

CMD ["sh", "./start.sh"]
