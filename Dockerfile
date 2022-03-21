FROM python:3.9

ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY . /code/
RUN apt-get update && apt-get upgrade -y && apt-get install -y -q binutils libproj-dev gdal-bin
RUN apt-get install libasound2 -y
RUN pip install -r requirements.txt
RUN pip install -e .
