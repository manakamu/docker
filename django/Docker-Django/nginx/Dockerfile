FROM nginx:1.21.3
 
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

RUN cp /usr/share/zoneinfo/Japan /etc/localtime

RUN apt update
RUN apt install emacs less -y
RUN apt install certbot -y
