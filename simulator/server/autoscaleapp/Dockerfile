FROM python:3.10.6-alpine3.15

ENV APP_HOME=/home/app/autoscaleapp

RUN mkdir -p $APP_HOME
RUN mkdir -p $APP_HOME/static

WORKDIR $APP_HOME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add postgresql-dev gcc python3-dev musl-dev \
    && apk del build-deps \
    && apk --no-cache add musl-dev linux-headers g++
RUN pip install --upgrade pip

COPY . $APP_HOME
RUN pip install -r requirements.txt
COPY ./entrypoint.sh $APP_HOME

CMD ["/bin/bash", "/home/app/autoscaleapp/entrypoint.sh"]
