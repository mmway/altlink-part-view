from django import template

register = template.Library()
@register.filter()
def vote_if_voted(obj, user):
    return obj.vote_if_user_voted(user)