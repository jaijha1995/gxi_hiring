python manage.py makemigrations
python manage.py migrate
python manage.py runserver 127.0.0.1:8080

celery -A restserver worker -l info -c 10 

uvicorn restserver.asgi:application --host 0.0.0.0 --port 8002 --reload