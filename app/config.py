import os

# Authentification Database
config_auth_psql = {
    "host": os.getenv("EV_PSQL_HOST", default="localhost"),
    "port": os.getenv("EV_PSQL_PORT", default="5432"),
    "database": os.getenv("EV_PSQL_DATABASE", default=None),
    "user": os.getenv("EV_PSQL_USERNAME", default="postgres"),
    "password": os.getenv("EV_PSQL_PASSWORD", default=None)
}

# Postgres Evidence Database
config_ev_psql = {
    "host": os.getenv("EV_PSQL_HOST", default="localhost"),
    "port": os.getenv("EV_PSQL_PORT", default="5432"),
    "database": os.getenv("EV_PSQL_DATABASE", default=None),
    "user": os.getenv("EV_PSQL_USERNAME", default="postgres"),
    "password": os.getenv("EV_PSQL_PASSWORD", default=None)
}
