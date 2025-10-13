python manage.py runserver 192.168.10.194:8085

celery -A restserver worker -l info -c 10 

uvicorn restserver.asgi:application --host 0.0.0.0 --port 8000 --reload