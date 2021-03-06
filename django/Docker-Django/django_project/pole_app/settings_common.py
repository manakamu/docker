import os

from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'kw!a&i1+&n(kqqlsq5+%zx#s*k5ajyi+vs!$urw#g!9jgse8wl'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'pole.apps.PoleConfig',
    'accounts.apps.AccountsConfig',

    'django.contrib.sites',
    'allauth',
    'allauth.account',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pole_app.urls'

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
        },
    },
]

WSGI_APPLICATION = 'pole_app.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
    'poleBlogDB': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'poleBlog.db'),
    },
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

#STATICFILES_DIRS = (
#    os.path.join(BASE_DIR, 'static'),
#)

MEDIA_URL = '/media/'

MESSAGE_TAGS = {
    messages.ERROR: 'alert alert-danger',
    messages.WARNING: 'alert alert-warning',
    messages.SUCCESS: 'alert alert-success',
    messages.INFO: 'alert alert-info',
}

AUTH_USER_MODEL = 'accounts.CustomUser'

# django-allauth???????????????django.contrib.sites????????????????????????????????????ID?????????
SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    'allauth.account.auth_backends.AuthenticationBackend',  # ?????????????????????(???????????????????????????)
    'django.contrib.auth.backends.ModelBackend',  # ??????????????????(?????????????????????)
)

# ????????????????????????????????????????????????
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False

# ?????????????????????????????????????????????????????????????????????
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True

# ????????????/???????????????????????????????????????
LOGIN_REDIRECT_URL = 'pole:top'
ACCOUNT_LOGOUT_REDIRECT_URL = 'account_login'

# ???????????????????????????????????????????????????????????????????????????
ACCOUNT_LOGOUT_ON_GET = True

# django-allauth????????????????????????????????????????????????????????????????????????????????????????????????
ACCOUNT_EMAIL_SUBJECT_PREFIX = ''

# ?????????????????????????????????????????????
DEFAULT_FROM_EMAIL = 'nasmanager55@gmail.com'

EMAIL_HOST = u'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = u'nasmanager55@gmail.com'
EMAIL_HOST_PASSWORD = u'lzmm oqxj uypj wauh'
EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
