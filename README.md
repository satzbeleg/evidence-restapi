# EVIDENCE project - REST API (fastapi)

Table of contents

- [Purpose](#purpose)
- [Installation](#installation)
- [Local Development](#local-development)
- [Unit Testing](#unit-testing)
- [Usage Examples](#usage-examples)
- [Authentication Process](#authentication-process)
- [Appendix](#appendix)


## Purpose
The REST API connects the [databases](https://github.com/satzbeleg/evidence-database) and the [web app](https://github.com/satzbeleg/evidence-app).

## Installation
Please follow the instruction of the [deployment repository](https://github.com/satzbeleg/evidence-deploy).


## Local Development
1. [Install Ubuntu / Debian packages](#install-ubuntu--debian-packages)
2. [Install FastAPI in a seperate virtual environment](#install-fastapi-in-a-seperate-virtual-environment)
3. [Configure environment variables](#configure-environment-variables)
4. [Start the database container](#start-the-database-container)
5. [Start the FastAPI Server](#start-the-fastapi-server)
6. [Check if the docker configuration of the REST API works](#check-if-the-docker-configuration-of-the-rest-api-works)

### Install Ubuntu / Debian packages

```bash
sudo apt update
sudo apt install -y --no-install-recommends build-essential python3-dev python3-venv
sudo apt install -y --no-install-recommends libpq-dev
```


### Install FastAPI in a seperate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt
```


### Configure environment variables
In particular, the SMTP settings must be adapted.

```bash
set -a
source defaults.env.sh
# source specific.env.sh

export CORS_WEBAPP_HOSTPORT=55018

export DBAPPL_HOST=localhost
export DBAPPL_PORT=55015
export DBAPPL_USER=postgres

export DBAUTH_HOST=localhost
export DBAUTH_PORT=55014
export DBAUTH_USER=postgres
```


### Start the database container
Follow instructions in [databases](https://github.com/satzbeleg/evidence-database) or [deployment repository](https://github.com/satzbeleg/evidence-deploy) (without loading `restapi.yml`)


### Start the FastAPI Server

```bash
source .venv/bin/activate
uvicorn app.main:app --host localhost --port 55017 --reload --log-level debug
```

Open [http://localhost:55017/v1/docs](http://localhost:55017/v1/docs) in your browser.


### Check if the docker configuration of the REST API works

```sh
docker-compose -p evidence2 -f network.yml -f restapi.yml up --build
```



## Unit Testing

### Start the database container
See [Start the database container](#configure-environment-variables)

### Add Test Email-Account directly in the database
In order to carry out the unit tests, a test account is created directly in the Postgres database. 
The test user has the email `nobody@example.com` and the password is `supersecret`.
**Never** do this on a production server!

We assume that the container of the authentication database is running at `localhost:55014`.

```sh
psql --host=127.0.0.1 --port=55014 --username=postgres -f test/addtestaccount.sql
```

### Load the Environment Variables
See [Configure environment variables]()

### Run Unit Tests
```sh
source .venv/bin/activate
pytest
```




## Usage Examples

### From the command line
Authenticate yourself with the test account. Request an access token.

```bash
curl -X POST "http://0.0.0.0:55017/v1/auth/login" \
    -H "accept: application/json" -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=nobody@example.com&password=supersecret" \
    > mytokendata
cat mytokendata
TOKEN=$(cat mytokendata | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN
```

Try other Requests

```bash
curl -X GET "http://127.0.0.1:55017/v1/bestworst/random/4" \
    -H "accept: application/json" \
    -H "Authorization: Bearer ${TOKEN}"

curl -X POST "http://localhost:55017/v1/user/settings" \
    -H  "accept: application/json" -H  "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" -d '{"hello":"world3"}'

curl -X GET "http://localhost:55017/v1/user/settings" \
    -H  "accept: application/json" -H  "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}"

curl -X POST "http://localhost:55017/v1/bestworst/samples/4/3/100/0" \
    -H  "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{"lemmata": ["Fahrrad"]}'

curl -X POST "http://localhost:55017/v1/user/settings" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{"test": 123}'
```


### In Python

```python
import requests
data = {"username": "nobody@example.com", "password": "supersecret"}
resp = requests.post("http://localhost:55017/v1/auth/login", data)
print(resp.text)

TOKEN = resp.json()['access_token']
headers = {'Authorization': f"Bearer {TOKEN}"}

resp = requests.get("http://localhost:55017/v1/bestworst/random/5", headers=headers)
print(resp.json())
```




## Authentication Process
The authentication mechanism is implemented in

- the [databases](https://github.com/satzbeleg/evidence-database) repository: `dbauth/` and `dbauth.yml`
- the REST API repository: `app/routers/auth_email.py` and `restapi.yml`

It is very important to setup the SMTP credentials to send verfication emails in `specific.env.sh`

### The Authentification Workflow
- In the UI, the user enters his email and desired password and sends it to the API
- API: Email / PW is forwarded to DB
- DB creates an inactive user account and returns verification token and API.
- API sends email with verification link to the specified email
- User clicks verification link
- API reads verification tokens and sends them to the DB
- DB checks verification token and sets user account to active.

### Create a new user account (register)
Bitte ersetze `you@example.com` durch eine gültige Email.

```sh
EMAIL=you@example.com
PASSWORD=secret2
curl -X POST "http://0.0.0.0:55017/v1/auth/register" \
    -H "accept: application/json" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${EMAIL}&password=${PASSWORD}"
```

### Process verfication link (verify)
Please use the link in your email inbox.

```sh
VERIFYTOKEN=273950a0-a11a-461b-83b3-12ddd1b1d9b5
curl -X GET "http://0.0.0.0:55017/v1/auth/verify/${VERIFYTOKEN}"
```

#### Log in (login)

```bash
curl -X POST "http://0.0.0.0:55017/v1/auth/login" \
    -H "accept: application/json" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${EMAIL}&password=${PASSWORD}" > mytokendata
TOKEN=$(cat mytokendata | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN
```



## Appendix

### Documentation
- Show the docs `http://localhost:55017/docs`
- Show Redoc: `http://localhost:55017/redoc`


### Commands
- Check pip8 syntax: `flake8 --ignore=F401 --exclude=$(grep -v '^#' .gitignore | xargs | sed -e 's/ /,/g')`
- Run unit tests: `pytest`

Clean Up code

```bash
find . -type f -name "*.pyc" | xargs rm
find . -type d -name "__pycache__" | xargs rm -r
rm -r .pytest_cache
rm -r .venv
```

### Support
Please [open an issue](https://github.com/satzbeleg/evidence-restapi/issues/new) for support.

### Contributing
Please contribute using [Github Flow](https://guides.github.com/introduction/flow/). Create a branch, add commits, and [open a pull request](https://github.com/satzbeleg/evidence-restapi/compare/).

