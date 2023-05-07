FROM python:3.11-slim-buster

RUN apt-get update --allow-unauthenticated
RUN apt-get install -y build-essential libssl-dev ca-certificates libasound2 wget --allow-unauthenticated

WORKDIR /doc_blog
RUN pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV HOST 0.0.0.0


CMD flask --app doc_blog run --host $HOST --port $PORT

#CMD [ "flask", "--app", "doc_blog", "run", "--debug", "--host=0.0.0.0", "--port=8080"]