FROM python:3.9.7

WORKDIR /app
ENV FLASK_APP=app

RUN cp /usr/share/zoneinfo/Japan /etc/localtime

COPY ./flaskapp/requirements.txt ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
