from django.apps import AppConfig

class CotisationtontineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cotisationtontine'

    def ready(self):
        import cotisationtontine.signals


