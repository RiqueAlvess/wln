from django.templatetags.static import static
from django.urls import reverse
from django.contrib.messages import get_messages
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': reverse,
        'get_messages': get_messages,
    })

    env.filters.update({
        'datetimeformat': lambda value, fmt='%d/%m/%Y %H:%M': value.strftime(fmt) if value else '',
        'dateformat': lambda value, fmt='%d/%m/%Y': value.strftime(fmt) if value else '',
        'truncate': lambda value, length=50: value[:length] + '...' if len(value) > length else value,
        'tojson': lambda value: __import__('json').dumps(value),
    })

    return env


def jinja2_context_processor(request):
    from apps.core.context_processors import branding
    return branding(request)
