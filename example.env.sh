#!/bin/bash 

# Host Server's Port Settings
export RESTAPI_HOSTPORT=55017

# Postgres Settings
# WARNING: You need to start the database container first
export DBAPPL_PASSWORD=password1234
export DBAUTH_PASSWORD=password1234

# REST API Settings
export RESTAPI_NUM_WORKERS=1
export RESTAPI_SECRET_KEY=$(openssl rand -hex 32)
export RESTAPI_TOKEN_EXPIRY=1440  # in minutes

# WEB APP Settings
export WEBAPP_HOSTPORT=55018
export WEBAPP_EXTERNAL_URL=localhost
#export WEBAPP_EXTERNAL_URL=evidence.bbaw.de

