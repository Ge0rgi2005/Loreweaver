from django.urls import path
from .views import choice_delete

app_name = "choices"

urlpatterns = [
    path("<int:pk>/delete/", choice_delete, name="delete"),
]