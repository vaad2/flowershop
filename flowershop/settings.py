# Django settings for vestlitecms project.
import os, sys

ALLOWED_HOSTS = ['www.flowershop.ru', 'flowershop.ru']

PROJECT_ROOT = PROJECT_PATH = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]
sys.path.append('%s/../vest' % PROJECT_ROOT)

ADMINS = (
# ('Your Name', 'your_email@example.com'),
)

APP_DATA = {
    'version': '0.1'
}

MANAGERS = ADMINS


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Moscow'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru'

LANGUAGES = (
    ('ru', 'Russian'),
    ('en', 'English'),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = '%s/media' % PROJECT_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = "%s/static_remote" % PROJECT_ROOT

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    '%s/static' % PROJECT_ROOT,
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
# from django.contrib.staticfiles.finders import AppDirectoriesFinder
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.

SECRET_KEY = 'kj9v9k+an2b@c$_s23#-(commwdrj7t*mo(*12y)k'
# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'common.loaders.load_template_source',
    'django.template.loaders.filesystem.Loader',

    'django.template.loaders.app_directories.Loader',

    #     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'common.middleware.MiddlewareMultipleProxy',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'common.middleware.MiddlewareAjaxCSRFDisable',
    'common.middleware.MiddlewareThreadLocal',
    'common.middleware.MiddlewareSite',
    'common.middleware.MiddlewareView',
    'common.middleware.MiddlewareAppData',
    'common.middleware.MiddlewareFilterPersist',
    'flowershop.middleware.MiddlewareCachedTree',
    'flowershop.middleware.MiddlewareSimplePage',
    'flowershop.middleware.MiddlewareCategory',
    'flowershop.middleware.MiddlewareBasket'

    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'flowershop.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'flowershop.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'grappelli.dashboard',
    'grappelli',
    'filebrowser',
    'django.contrib.admin',
    'frontend',
    'common',
    'south',
    'password_reset',

    'sorl.thumbnail',
    'sorl_watermarker'
    #'robokassa',


)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'flowershop.context_processors.cached_tree')
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
        # 'file': {
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'level': 'DEBUG',
        #     'filename': '%s/log.log' % PROJECT_ROOT
        # }
    },
    'loggers': {

        'flowershop.views': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },

        'flowershop.models': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
        'flowershop.commands' : {
            'handlers': ['console'],
            'level': 'DEBUG'

        }

        # 'vest.common.urls': {
        #     'handlers': ['file'],
        #     'level': 'DEBUG'
        # }

        #        'django.request': {
        #            'handlers': ['mail_admins'],
        #            'level': 'ERROR',
        #            'propagate': True,
        #        },
        # '': {
        #     'handlers': ['file'],
        #     'level': 'DEBUG'
        # }
        #        'django.db.backends':{
        #                    'handlers': ['file'],
        #                    'level': 'DEBUG'
        #                }

    }
}

ADMIN_MEDIA_PREFIX = '/static/admin/'

MONGO = {
    'default': {
        'NAME': 'dbflowershop'
    }
}

GRAPPELLI_INDEX_DASHBOARD = {
    'flowershop.admin_super.admin_super': 'flowershop.dashboard_super.CustomIndexDashboard',
    'flowershop.admin_client.admin_client': 'flowershop.dashboard_client.CustomIndexDashboard',

}

LOCALE_PATHS = (
    '%s/locale' % PROJECT_ROOT,
    '%s/../vest/locale' % PROJECT_ROOT,
)


#sorl.thumbnail.engines.pil_engine.Engine'

#import sorl
#sorl.thumbnail.engines.pil_engine.Engine
THUMBNAIL_ENGINE = 'sorl_watermarker.engines.pil_engine.Engine'
THUMBNAIL_WATERMARK = 'watermark.png'
THUMBNAIL_WATERMARK_POSITION = 'center'
THUMBNAIL_WATERMARK_ALWAYS = False

SIMPLE_PAGE_TEMPLATE = 'base_page.html'

import socket

HOSTS = ['ld1', 'ld2', 'ld-mac.loc']
LOCAL = False

ROBOKASSA_TEST_MODE = True
if not socket.gethostname() in HOSTS:
    from settings_remote import *
else:
    from settings_local import *

# from django.core.files.storage import
# django/core/files/storage.py