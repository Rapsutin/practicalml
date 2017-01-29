FROM python:3.6

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt


COPY . /usr/src/app
RUN python manage.py collectstatic --noinput
CMD gunicorn -b 0.0.0.0:8000 practicalml.wsgi:application
