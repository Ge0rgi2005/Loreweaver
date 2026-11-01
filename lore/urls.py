from django.urls import path
from . import views

app_name = "lore"

urlpatterns = [
    path("", views.lore_entry_list, name="list"),
    path("add/", views.create_lore_entry, name="create"),
    path("<int:pk>/", views.lore_entry_detail, name="detail"),
    path("<int:pk>/edit/", views.edit_lore_entry, name="edit"),
    path("<int:pk>/delete/", views.delete_lore_entry, name="delete"),
]