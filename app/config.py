import os
import secrets

# Postgres Evidence Database
config_ev_psql = {
    "host": os.getenv("DBAPPL_HOST", default=None),  # localhost
    "port": os.getenv("DBAPPL_PORT", default=None),  # 5432
    "database": os.getenv("DBAPPL_DATABASE", default=None),
    "user": os.getenv("DBAPPL_USER", default="postgres"),
    "password": os.getenv("DBAPPL_PASSWORD", default=None)
}

# Web App Settings (e.g. CORS)
config_web_app = {
    "port": os.getenv("CORS_WEBAPP_HOSTPORT", default="8080"),
    "domain": os.getenv("CORS_WEBAPP_DOMAIN", default="localhost")
}

# Authentification Database
# see database/dbauth.yml 
config_auth_psql = {
    "host": os.getenv("DBAUTH_HOST", default=None),  # localhost
    "port": os.getenv("DBAUTH_PORT", default=None),  # 5432
    "database": os.getenv("DBAUTH_DATABASE", default=None),
    "user": os.getenv("DBAUTH_USER", default="postgres"),
    "password": os.getenv("DBAUTH_PASSWORD", default=None)
}

# Access Token Settings
# - How to create a SECRET_KEY: `openssl rand -hex 32`
config_auth_token = {
    "SECRET_KEY": os.getenv(
        "ACCESS_SECRET_KEY", default=secrets.token_hex(32)),
    "ALGORITHM": os.getenv("ACCESS_ALGORITHM", default="HS256"),
    "TOKEN_EXPIRY": os.getenv("ACCESS_TOKEN_EXPIRY", default=1440)  # minutes
}

# Mailer settings for Verfication Mails
cfg_mailer = {
    "SMTP_SERVER": os.getenv("SMTP_SERVER", default=None),
    "SMTP_PORT": os.getenv("SMTP_PORT", default=None),
    "SMTP_TLS": os.getenv("SMTP_TLS", default=None),
    "SMTP_USER": os.getenv("SMTP_USER", default=None),
    "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD", default=None),
    "FROM_EMAIL": os.getenv("FROM_EMAIL", default=None),
    "VERIFY_PUBLIC_URL": os.getenv("VERIFY_PUBLIC_URL", default=None),
}
