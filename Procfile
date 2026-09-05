release: python manage.py migrate --noinput && python manage.py collectstatic --no-input
web: gunicorn canidoit.wsgi
worker: python manage.py db_worker --settings=canidoit.settings.prod
