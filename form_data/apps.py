from django.apps import AppConfig


class FormDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'form_data'

    def ready(self):
        import form_data.signals  # noqa
        import form_data.signals_task     # n
