from django import template

register = template.Library()

@register.filter
def reading_time(text):
    words = text.split()
    word_count = len(words)
    reading_time_minutes = word_count / 200
    return round(reading_time_minutes, 2)

@register.inclusion_tag('partials/_form.html')
def story_badge(story):
    return {'story': story}