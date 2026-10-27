from django.urls import path
from . import views

app_name = "lore"

urlpatterns = [
    path("", views.lore_list, name="list"),
    path("add/", views.lore_create, name="create"),
    path("<int:pk>/", views.lore_detail, name="detail"),
    path("<int:pk>/edit/", views.lore_edit, name="edit"),
    path("<int:pk>/delete/", views.lore_delete, name="delete"),
]