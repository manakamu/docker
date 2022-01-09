FROM nginx:1.21.3
 
#RUN rm /etc/nginx/conf.d/default.conf
COPY ssl.conf /etc/nginx/conf.d/ssl.conf

RUN cp /usr/share/zoneinfo/Japan /etc/localtime

RUN apt update
RUN apt install emacs less -y
RUN apt install certbot -y

COPY server.crt /etc/nginx/conf.d/
COPY server.key /etc/nginx/conf.d/
COPY server.password /etc/nginx/conf.d/

RUN rm /var/log/nginx/*

RUN apt install certbot 
#RUN certbot --no-bootstrap certonly --webroot -w /usr/src/app/web -d indigoblue3.ddns.net -m manakamu2012@gmail.com --agree-tos
