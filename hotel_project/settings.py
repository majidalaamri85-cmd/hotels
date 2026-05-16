from pathlib import Path
import os, dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

default_hosts = ['127.0.0.1', 'localhost']
env_hosts = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]
render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_hostname:
    env_hosts.append(render_hostname)
ALLOWED_HOSTS = env_hosts or default_hosts

csrf_origins = [o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
if render_hostname:
    csrf_origins.append(f"https://{render_hostname}")
CSRF_TRUSTED_ORIGINS = csrf_origins

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'evaluations'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # Enable GZIP compression
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',  # Support for cache validation
    'evaluations.middleware.PerformanceOptimizationMiddleware',
    'evaluations.middleware.MobileOptimizationMiddleware',
    'evaluations.middleware.SecurityHeadersMiddleware',
]

ROOT_URLCONF = 'hotel_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ] if not DEBUG else None,
        }
    }
]

WSGI_APPLICATION = 'hotel_project.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", 
        conn_max_age=600,
    )
}

# Cache configuration
if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'OPTIONS': {
                'MAX_ENTRIES': 1000
            }
        }
    }
else:
    # Allow explicit override when running without cache table in some environments.
    cache_backend = os.environ.get('CACHE_BACKEND', 'db').lower()
    if cache_backend == 'locmem':
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'prod-fallback-cache',
            }
        }
    else:
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'django_cache',
            }
        }

# Cache timeout settings (in seconds)
CACHE_TIMEOUT = 300  # 5 minutes default

# Database optimization
if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    DATABASES['default']['OPTIONS'] = {
        'timeout': 30,
    }

LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Muscat'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise optimization for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = True
WHITENOISE_COMPRESSION_QUALITY = 80
WHITENOISE_COMPRESSION_OFFLINE = True
WHITENOISE_KEEP_ONLY_LATEST_FILES = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Image optimization
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = int(os.environ.get('DATA_UPLOAD_MAX_NUMBER_FIELDS', 10000))
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
IMAGE_MIN_SIZE = (100, 100)
IMAGE_MAX_SIZE = (2000, 2000)

# Session optimization
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1209600  # 2 weeks

# Security settings
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", 'cdn.jsdelivr.net'),
    'style-src': ("'self'", 'cdn.jsdelivr.net', "'unsafe-inline'"),
    'font-src': ("'self'", 'fonts.googleapis.com', 'fonts.gstatic.com', 'cdn.jsdelivr.net'),
    'img-src': ("'self'", 'data:', 'https:'),
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/admin/login/'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
} if DEBUG else {}
