from django.urls import path
from . import views

app_name = "stories"

urlpatterns = [
    path("", views.StoryListView.as_view(), name="list"),
    path("add/", views.StoryCreateView.as_view(), name="create"),
    path("<int:pk>/", views.StoryDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.StoryUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.StoryDeleteView.as_view(), name="delete"),

    path(
        "<int:story_pk>/scenes/add/",
        views.SceneCreateView.as_view(),
        name="scene_create",
    ),
]