FROM python:3.9.7

WORKDIR /app
ENV FLASK_APP=app

COPY ./flaskapp/requirements.txt ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
