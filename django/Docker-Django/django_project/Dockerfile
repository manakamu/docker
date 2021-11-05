# BUILDER #
 
FROM python:3.8.12-bullseye as builder

USER root

WORKDIR /usr/src/app
 
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
 
#RUN apk update \
#    && apk add postgresql-dev gcc python3-dev musl-dev
 
RUN pip install --upgrade pip
RUN pip install flake8
COPY . .
 
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt
 
 
# FINAL #
 
FROM python:3.8.12-bullseye

USER root

RUN mkdir -p /usr/src/app
 
#RUN addgroup -S app && adduser -S app -G app
 
ENV HOME=/usr/src/app
ENV APP_HOME=/usr/src/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME
 
#RUN apk update && apk add libpq
RUN apt-get update
RUN apt-get install emacs -y
RUN apt-get install less -y

COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache /wheels/*

COPY . $APP_HOME

#RUN chown -R app:app $APP_HOME

#USER app

#ENTRYPOINT ["/home/app/web/entrypoint.sh"]

RUN cp /usr/share/zoneinfo/Japan /etc/localtime