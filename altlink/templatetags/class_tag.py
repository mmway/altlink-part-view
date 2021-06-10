from django import template

register = template.Library()

@register.filter(name='get_class_name')
def get_class_name(value):
    return value.__class__.__name__

@register.filter(name='get_class')
def get_class(value):
    return value.__class__