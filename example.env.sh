#!/bin/bash 

# Host Server's Port Settings
export RESTAPI_HOSTPORT=55017

# Performance Settings
export RESTAPI_NUM_WORKERS=1

# Application Database
# - see database/dbappl.yml
echo "WARNING: Make sure that the dbappl.yml Container is running!"
export DBAPPL_PASSWORD=password1234

# CORS Exemption Settings
# - see webapp/webapp.yml
export WEBAPP_HOSTPORT=55018
export WEBAPP_PUBLIC_URL=localhost

# Authentification Database
# - see database/dbauth.yml 
echo "WARNING: Make sure that the dbauth.yml Container is running!"
export DBAUTH_PASSWORD=password1234

# Access Token Settings
export ACCESS_SECRET_KEY=$(openssl rand -hex 32)
export ACCESS_TOKEN_EXPIRY=1440  # in minutes

# Mailer settings for Verfication Mails
echo "WARNING: Please specify a real SMTP Mail Account!"
export SMTP_SERVER="smtp.example.com"
export SMTP_PORT=587
export SMTP_TLS=1
export SMTP_USER="nobody"
export SMTP_PASSWORD="supersecret"
export FROM_EMAIL="nobody@example.com"

echo "WARNING: Specify the real base URL of the WebApp lateron"
export VERIFY_PUBLIC_URL="http://localhost:${RESTAPI_HOSTPORT}"
#export VERIFY_PUBLIC_URL="http://${WEBAPP_PUBLIC_URL}:${WEBAPP_HOSTPORT}"
