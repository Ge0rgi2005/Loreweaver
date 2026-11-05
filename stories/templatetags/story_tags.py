import math

from django import template

register = template.Library()


@register.filter
def reading_time(text):
    if not isinstance(text, str):
        return ""
    words = text.split()
    reading_time_minutes = max(1, math.ceil(len(words) / 200))
    return f"{reading_time_minutes} min read"


@register.inclusion_tag("partials/_story_badges.html")
def story_badges(story):
    return {"story": story}