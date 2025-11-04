from django.urls import re_path
from .consumers import TypeformRealtimeConsumer
from google_form_work.consumers import GoogleFormAllSheetsConsumer
from form_data.consumer.consumers import FormDataRealtimeConsumer
from form_data.consumer.consumers_realtime_model import FormDataModelRealtimeConsumer
from tasks.consumers import TaskConsumer


websocket_urlpatterns = [
    re_path(r'ws/$', TypeformRealtimeConsumer.as_asgi()),
    re_path(r"ws/forms/$", GoogleFormAllSheetsConsumer.as_asgi()),
    re_path(r'^ws/formdata/$', FormDataRealtimeConsumer.as_asgi()),
    re_path(r'^ws/formdata_model/$', FormDataModelRealtimeConsumer.as_asgi()),
    re_path(r"ws/tasks/$", TaskConsumer.as_asgi()),
]
