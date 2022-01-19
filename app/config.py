import os
import secrets

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

# Config will be read from environment variables and/or ".env" files.
config = Config(".env")

# Postgres Evidence Database
config_ev_psql = {
    "host": config("DBAPPL_HOST", default='localhost'),
    "port": config("DBAPPL_PORT", cast=int, default='5432'),
    "database": config("DBAPPL_DATABASE", default=None),
    "user": config("DBAPPL_USER", default="evidence"),
    "password": config("DBAPPL_PASSWORD", default="evidence")
}

# Web App Settings (e.g. CORS)
config_web_app = {
    "port": os.getenv("CORS_WEBAPP_HOSTPORT", default="8080"),
    "domain": os.getenv("CORS_WEBAPP_DOMAIN", default="localhost")
}

# Authentication Database
# see database/dbauth.yml
config_auth_psql = {
    "host": config("DBAUTH_HOST", default='localhost'),
    "port": config("DBAUTH_PORT", cast=int, default='5432'),
    "database": config("DBAUTH_DATABASE", default=None),
    "user": config("DBAUTH_USER", default="evidence"),
    "password": config("DBAUTH_PASSWORD", default="evidence")
}

# Access Token Settings
# - How to create a SECRET_KEY: `openssl rand -hex 32`
config_auth_token = {
    "SECRET_KEY": config("ACCESS_SECRET_KEY", default=secrets.token_hex(32)),
    "ALGORITHM": config("ACCESS_ALGORITHM", default="HS256"),
    "TOKEN_EXPIRY": config("ACCESS_TOKEN_EXPIRY", cast=int, default=1440)
}

# Mailer settings for Verification Mails
cfg_mailer = {
    "SMTP_SERVER": config("SMTP_SERVER", default='localhost'),
    "SMTP_PORT": config("SMTP_PORT", cast=int, default="25"),
    "SMTP_TLS": config("SMTP_TLS", cast=bool, default="0"),
    "SMTP_USER": config("SMTP_USER", default=None),
    "SMTP_PASSWORD": config("SMTP_PASSWORD", default=None),
    "FROM_EMAIL": config("FROM_EMAIL", default='evidence-app@bbaw.de'),
    "VERIFY_PUBLIC_URL": config("VERIFY_PUBLIC_URL",
                                default='http://localhost:8080')
}
