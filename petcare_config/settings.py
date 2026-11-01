"""
Configuración principal de Django para el sistema veterinario PetCare (EVA 3).
Alumno: Angel Eduardo Lara Manriquez
Sección: IEC-N4-C2
Docente: Marcelo Alvarado Aravena
Año: 2026
"""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-petcare-eva3-2026-angel-lara-key'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
if os.environ.get('EC2_PUBLIC_IP'):
    CSRF_TRUSTED_ORIGINS.extend([
        f"http://{os.environ['EC2_PUBLIC_IP']}",
        f"https://{os.environ['EC2_PUBLIC_IP']}",
    ])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Librerías de terceros (DRF, Filtros, JWT, OpenAPI)
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',

    # Aplicaciones del dominio PetCare
    'users',
    'clinica',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'petcare_config.middleware.RedirectUnknownRoutesMiddleware',
]

ROOT_URLCONF = 'petcare_config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'petcare_config.wsgi.application'
ASGI_APPLICATION = 'petcare_config.asgi.application'

# Conexión relacional nativa con PostgreSQL (Criterio 1 de la Rúbrica)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'petcare_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'inacap.2030'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

AUTH_USER_MODEL = 'users.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de Django REST Framework (Sesiones + JWT + Filtros)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'PetCare API - Clínica Veterinaria',
    'DESCRIPTION': (
        'Sistema integral de Gestión de Tutores, Mascotas, Agendamiento de Citas sin solapamiento, '
        'Fichas Clínicas Digitales y Recordatorios de Vacunación.\n\n'
        '**Evaluación Parcial N°3 - Desarrollo Backend**\n'
        '- **Alumno:** Angel Eduardo Lara Manriquez\n'
        '- **Docente:** Marcelo Alvarado Aravena\n'
        '- **Año:** 2026'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
    },
}
