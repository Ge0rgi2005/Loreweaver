from django.urls import path
from . import views

app_name = "scenes"

urlpatterns = [
    path("<int:pk>/", views.SceneDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.SceneUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.SceneDeleteView.as_view(), name="delete"),
    path(
        "<int:scene_pk>/choices/add/",
        views.create_choice,
        name="choice_create",
    ),
]