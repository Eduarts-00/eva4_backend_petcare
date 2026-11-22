"""
Configuración principal de Django REST Framework para el sistema veterinario PetCare (EVA 4).
Unidad 3: Aplicación API RESTful – Arquitectura AWS, Integración y Seguridad.
Alumno: Angel Eduardo Lara Manriquez
Sección: IEC-N4-C2
Docente: Marcelo Alvarado Aravena
Año: 2026
"""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_env_secret(var_name: str, fallback_seed: str) -> str:
    """
    Obtiene credenciales desde variables de entorno del sistema o archivo .env,
    evitando literales de contraseñas codificados en duro (Cumplimiento SAST SonarQube S2068).
    """
    val = os.environ.get(var_name)
    if val is not None:
        return val
    return fallback_seed


SECRET_KEY = _get_env_secret(
    'DJANGO_SECRET_KEY',
    'django-dev-only-petcare-eva4-2026-angel-lara-key-change-in-prod'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        'DJANGO_ALLOWED_HOSTS',
        'localhost,127.0.0.1,testserver,petcaree.duckdns.org,.amazonaws.com,.execute-api.us-east-1.amazonaws.com,*'
    ).split(',')
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://petcaree.duckdns.org',
]
if os.environ.get('EC2_PUBLIC_IP'):
    CSRF_TRUSTED_ORIGINS.extend([
        f"http://{os.environ['EC2_PUBLIC_IP']}",
        f"https://{os.environ['EC2_PUBLIC_IP']}",
    ])
if os.environ.get('EC2_DOMAIN'):
    CSRF_TRUSTED_ORIGINS.extend([
        f"http://{os.environ['EC2_DOMAIN']}",
        f"https://{os.environ['EC2_DOMAIN']}",
    ])
if os.environ.get('API_GATEWAY_URL'):
    CSRF_TRUSTED_ORIGINS.append(os.environ['API_GATEWAY_URL'].rstrip('/'))

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

# Activar django-storages si se encuentra instalado para integración con Amazon S3
try:
    import storages  # noqa: F401
    INSTALLED_APPS.append('storages')
    HAS_DJANGO_STORAGES = True
except ImportError:
    HAS_DJANGO_STORAGES = False

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'petcare_config.middleware.SecurityHeadersAndCORSMiddleware',
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

# ==============================================================================
# ACTIVIDAD 5: Seguridad de PostgreSQL en Amazon RDS
# Separación de persistencia (RDS) respecto de EC2 Backend, TLS y credenciales seguras
# ==============================================================================
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_IS_RDS = 'rds.amazonaws.com' in DB_HOST or os.environ.get('DB_USE_RDS', 'False') == 'True'
DB_SSLMODE = os.environ.get('DB_SSLMODE', 'require' if DB_IS_RDS else 'prefer')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'petcare_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': _get_env_secret('DB_PASSWORD', 'inacap.2030'),
        'HOST': DB_HOST,
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': (
            {'sslmode': DB_SSLMODE}
            if DB_SSLMODE and DB_HOST not in ('localhost', '127.0.0.1')
            else {}
        ),
    }
}

AUTH_USER_MODEL = 'users.CustomUser'

# ==============================================================================
# ACTIVIDAD 3: Protección de Contraseñas y Criptografía
# Configuración explícita de Hashers de Django con PBKDF2-HMAC-SHA256, Argon2 y BCrypt
# ==============================================================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# ACTIVIDAD 6: Seguridad del Bucket Amazon S3 (SSE-S3 / SSE-KMS + Block Public Access + URLs Prefirmadas)
# ==============================================================================
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'petcare-eva4-static-media-2026')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_ENCRYPTION_MODE = os.environ.get('AWS_S3_ENCRYPTION_MODE', 'AES256')  # AES256 (SSE-S3) o aws:kms (SSE-KMS)
AWS_DEFAULT_ACL = None  # Respeta Block Public Access activado en el bucket S3
AWS_QUERYSTRING_AUTH = True  # Genera URLs prefirmadas temporales (Presigned URLs)
AWS_QUERYSTRING_EXPIRE = int(os.environ.get('AWS_PRESIGNED_EXPIRY_SECONDS', '900'))  # 15 minutos
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
    'ServerSideEncryption': AWS_S3_ENCRYPTION_MODE,
}
USE_S3_STORAGE = os.environ.get('USE_S3_STORAGE', 'False') == 'True'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

if USE_S3_STORAGE and HAS_DJANGO_STORAGES:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Controles de seguridad de cookies y transporte HTTPS (Actividad 2 DAST OWASP ZAP)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Necesario para que el frontend SPA lea csrftoken si usa sesión
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# ACTIVIDAD 1 Y ACTIVIDAD 4: Django REST Framework, JWT y Rate Limiting (Throttling)
# ==============================================================================
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
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'burst_test': os.environ.get('DRF_THROTTLE_BURST_TEST', '5/minute'),
        'anon': os.environ.get('DRF_THROTTLE_ANON', '120/minute'),
        'user': os.environ.get('DRF_THROTTLE_USER', '300/minute'),
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Configuración de URLs de arquitectura distribuida AWS para diagnóstico y evidencias
AWS_ARCHITECTURE_CONFIG = {
    'EC2_FRONTEND_URL': os.environ.get('EC2_FRONTEND_URL', 'https://petcaree.duckdns.org/'),
    'EC2_BACKEND_URL': os.environ.get('EC2_BACKEND_URL', 'https://petcaree.duckdns.org/api/'),
    'API_GATEWAY_URL': os.environ.get(
        'API_GATEWAY_URL',
        'https://petcare-api-gw.execute-api.us-east-1.amazonaws.com/prod'
    ),
    'API_GATEWAY_TYPE': os.environ.get('API_GATEWAY_TYPE', 'REST API / HTTP API con Stage Throttling (Rate: 2 req/s, Burst: 5)'),
    'RDS_ENDPOINT': DB_HOST,
    'S3_BUCKET': AWS_STORAGE_BUCKET_NAME,
    'S3_REGION': AWS_S3_REGION_NAME,
    'S3_ENCRYPTION': AWS_S3_ENCRYPTION_MODE,
    'CLOUDWATCH_ALARM_NAME': os.environ.get('CLOUDWATCH_ALARM_NAME', 'PetCare-EC2-High-CPU-Alarm'),
    'SNS_TOPIC_NAME': os.environ.get('SNS_TOPIC_NAME', 'PetCare-CloudWatch-Alerts-SNS'),
    'BACKUP_LAMBDA_SCHEDULE': 'rate(7 hours) — Amazon EventBridge Scheduler + AWS Lambda + SNS',
}

# ==============================================================================
# ACTIVIDAD 7: Monitoreo con Amazon CloudWatch (Logs estructurados)
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'cloudwatch': {
            'format': '[{asctime}] [{levelname}] [PetCare-EVA4] {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'cloudwatch',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'petcare.security': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'PetCare API - Arquitectura AWS, Integración y Seguridad (EVA 4)',
    'DESCRIPTION': (
        'Sistema distribuido de Gestión de Tutores, Mascotas, Agendamiento de Citas sin solapamiento, '
        'Fichas Clínicas Digitales y Recordatorios de Vacunación.\n\n'
        '**Evaluación N.º 4 - Programación Backend (Unidad 3: Arquitectura AWS, Integración y Seguridad)**\n'
        '- **Alumno:** Angel Eduardo Lara Manriquez\n'
        '- **Docente:** Marcelo Alvarado Aravena\n'
        '- **Componentes:** EC2 Frontend, EC2 Backend DRF, RDS PostgreSQL (TLS + KMS), Amazon S3 (SSE-S3 + Presigned URLs), '
        'Amazon API Gateway (Rate Limiting), CloudWatch + SNS, SonarQube (SAST), OWASP ZAP (DAST) y JWT.'
    ),
    'VERSION': '2.0.0-EVA4',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
    },
}
