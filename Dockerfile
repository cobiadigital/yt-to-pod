FROM python:3.11-slim-buster

WORKDIR /doc_blog
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV HOST 0.0.0.0
ENV PORT 5000

CMD flask --app doc_blog run --host $HOST --port $PORT
