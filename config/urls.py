from django.contrib import admin
from django.urls import include, path
from core.views import custom_404

handler404 = "core.views.custom_404"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("stories/", include("stories.urls")),
    path("scenes/", include("stories.scene_urls")),
    path(
        "choices/",
        include(
            ("stories.choice_urls", "choices"),
            namespace="choices",
        ),
    ),
    path("lore/", include("lore.urls")),
]