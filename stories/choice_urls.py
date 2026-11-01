from django.urls import path
from .views import delete_choice

app_name = "choices"

urlpatterns = [
    path("<int:choice_pk>/delete/", delete_choice, name="delete"),
]