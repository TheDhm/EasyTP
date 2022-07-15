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
RUN pip install gunicorn

# copy project
COPY ./Docker2CS ./Docker2CS
COPY ./main ./main
COPY ./manage.py .


RUN mkdir /READONLY
RUN mkdir /USERDATA

EXPOSE 8000
EXPOSE 587

#CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000"]
CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "Docker2CS.wsgi"]
