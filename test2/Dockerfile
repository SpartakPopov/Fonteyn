# syntax=docker/dockerfile:1

FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install -r requirements.txt
RUN chmod +x ./start.sh

EXPOSE 5000 5000

CMD ["./start.sh"]
