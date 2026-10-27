from django.urls import path
from . import views

app_name = "scenes"

urlpatterns = [
    path("<int:pk>/", views.SceneDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.SceneUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.SceneDeleteView.as_view(), name="delete"),
    path(
        "<int:scene_pk>/choices/add/",
        views.choice_create,
        name="choice_create",
    ),
]

choice_urlpatterns = [
    path(
        "<int:pk>/delete/",
        views.choice_delete,
        name="choice_delete",
    ),
]