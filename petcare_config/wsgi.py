"""
Configuración WSGI para despliegue con Gunicorn y Nginx en AWS EC2.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petcare_config.settings')

application = get_wsgi_application()
