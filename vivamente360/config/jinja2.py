from django.templatetags.static import static
from django.urls import reverse
from django.contrib.messages import get_messages
from django.middleware.csrf import get_token
from jinja2 import Environment
from markupsafe import Markup

from apps.core.context_processors import branding


def url_helper(viewname, *args, **kwargs):
    """
    Helper function for Jinja2 templates to reverse URLs.
    Accepts both positional and keyword arguments.
    """
    if args:
        return reverse(viewname, args=args)
    elif kwargs:
        return reverse(viewname, kwargs=kwargs)
    else:
        return reverse(viewname)


def csrf_input_helper(request):
    """
    Helper function to generate CSRF input field for Jinja2 templates.
    """
    token = get_token(request)
    return Markup(f'<input type="hidden" name="csrfmiddlewaretoken" value="{token}">')


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': url_helper,
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
    """
    Context processor para Jinja2 que integra os dados de branding.
    Este context processor adiciona variáveis de branding (empresa, logo, cores, etc.)
    disponíveis em todos os templates Jinja2.
    """
    context = branding(request)
    context['csrf_input'] = csrf_input_helper(request)
    return context
