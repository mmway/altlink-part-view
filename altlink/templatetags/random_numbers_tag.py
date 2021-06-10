import random
from django import template

register = template.Library()

@register.simple_tag
def random_int(a, b):
    if b is None:
        a, b = 0, a
    return random.randint(a, b)