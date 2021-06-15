import os

# Authentification Database
config_auth_psql = {
    "host": os.getenv("REST_DBAUTH_HOST", default="localhost"),
    "port": os.getenv("REST_DBAUTH_PORT", default="5432"),
    "database": os.getenv("REST_DBAUTH_DATABASE", default=None),
    "user": os.getenv("REST_DBAUTH_USER", default="postgres"),
    "password": os.getenv("REST_DBAUTH_PASSWORD", default=None)
}

# Postgres Evidence Database
config_ev_psql = {
    "host": os.getenv("REST_DBAPPL_HOST", default="localhost"),
    "port": os.getenv("REST_DBAPPL_PORT", default="5432"),
    "database": os.getenv("REST_DBAPPL_DATABASE", default=None),
    "user": os.getenv("REST_DBAPPL_USER", default="postgres"),
    "password": os.getenv("REST_DBAPPL_PASSWORD", default=None)
}

# Web App Settings (e.g. CORS)
config_web_app = {
    "port": os.getenv("CORS_WEBAPP_HOSTPORT", default="8080"),
    "host": os.getenv("CORS_WEBAPP_EXTERNAL_URL", default="localhost")
}
