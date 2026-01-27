from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

INSTALLED_APPS += [
    'django_extensions',
]

LOGGING['root']['level'] = 'DEBUG'
