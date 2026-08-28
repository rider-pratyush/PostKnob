from django.apps import AppConfig


class PostknobConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "postknob"
    verbose_name = "PostKnob"

    def ready(self):
        import postknob.signals  # noqa: F401 — connect signals