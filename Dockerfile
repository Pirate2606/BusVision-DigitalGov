FROM python:3.8-slim-buster

RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential wget ffmpeg libsm6
RUN apt-get install -y libxext6 

COPY . /app
WORKDIR /app

# Installing requirements
RUN pip3 install -r requirements.txt

# Downloading Dataset
RUN wget -q https://pjreddie.com/media/files/yolov3.weights

EXPOSE 5000
ENV PORT 5000

CMD exec gunicorn --bind :$PORT --workers 4 --threads 12 --timeout 0 app:app
#ENTRYPOINT exec gunicorn --bind :$PORT --workers 4 --threads 12 --timeout 0 app:app
