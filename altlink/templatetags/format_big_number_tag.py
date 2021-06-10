from django import template

register = template.Library()
@register.filter(name='format_big_number')
def format_big_number(value):
    if value != '':
        value_updated = value
        if pow(10, 6) <= abs(value) < pow(10, 9):
            value_updated = '{:.1f}'.format(value/1000) + "tys"
        if pow(10, 9) <= abs(value) < pow(10, 12):
            value_updated = '{:.1f}'.format(value/1000) + "mln"
        if pow(10, 12) <= abs(value) < pow(10, 15):
            value_updated = '{:.1f}'.format(value/1000) + "mld"
    else:
        value_updated = 'No number provided'

    return value_updated