# pull official base image
FROM python:3.9.10-alpine

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add -u gcc musl-dev
# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .

RUN python -m venv django
RUN source django/bin/activate

RUN pip install -r requirements.txt

# copy project
COPY . .

# use option -v /var/run/docker.sock:/var/run/docker.sock
RUN echo "" >> /var/run/docker.sock

RUN chmod 666 /var/run/docker.sock

EXPOSE 8000

CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000"]

