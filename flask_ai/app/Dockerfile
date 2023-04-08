FROM python:3.9.7

WORKDIR /app
ENV FLASK_APP=app

RUN cp /usr/share/zoneinfo/Japan /etc/localtime

COPY ./requirements.txt ./

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y libgl1-mesa-dev less

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN pip install -r ./yolov5/requirements.txt