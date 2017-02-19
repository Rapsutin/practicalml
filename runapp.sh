python manage.py migrate --noinput
gunicorn --daemon -b 0.0.0.0:8000 practicalml.wsgi:application
python manage.py run_huey
