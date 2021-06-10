from django import template

register = template.Library()
@register.filter()
def watch_if_watched(obj, user):
    return obj.watch_if_user_watched(user)