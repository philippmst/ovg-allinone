FROM python:3.11-alpine3.21

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

VOLUME [ "/usr/src/app" ]
RUN cd /usr/src/app

RUN apk update

RUN apk add py3-setuptools
RUN apk add postgresql-libs && \
apk add --virtual .build-deps python3-dev gcc musl-dev postgresql-dev
RUN apk add py-pip cmake
RUN apk add cairo 
RUN apk add cairo-dev

COPY requirements.txt .
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt --no-cache-dir
COPY ./mitgliederverwaltung /usr/src/app
RUN apk --purge del .build-deps

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8002"]

