from django import template

register = template.Library()

@register.filter
def get_type(value):
    try:
        return value.__class__.__name__
    except Exception as e:
        print("couldnt get class name %s " % e)
    return type(value)
