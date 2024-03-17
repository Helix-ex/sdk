FROM ubuntu:22.04
RUN apt-get update && apt-get -y install python3 python3-pip
WORKDIR /app

COPY . ./
RUN pip install -r requirements.txt

CMD bash