FROM ubuntu:latest
MAINTAINER Samuel Lee "samueljklee@gmail.com"
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential
COPY . /frontier-app
WORKDIR /frontier-app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["app.py"]