python manage.py runserver 127.0.0.1:8085

celery -A restserver worker -l info -c 10 