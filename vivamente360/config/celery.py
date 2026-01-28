import os
from pathlib import Path
from dotenv import load_dotenv
from celery import Celery

# Carrega variáveis de ambiente do arquivo .env
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('vivamente360')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
