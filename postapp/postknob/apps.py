from django.apps import AppConfig


class PostknobConfig(AppConfig):
    # default_auto_field = 'django.db.models.BigAutoField'
    name = 'postknob'
    
    def ready(self):
        import postknob.signals