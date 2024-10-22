# EVIDENCE project - REST API (fastapi)

Table of contents

- [Purpose](#purpose)
- [Installation](#installation)
- [Local Development](#local-development)
- [Check if the API is working](#check-if-the-api-is-working)
- [Authentication Process](#authentication-process)
- [Appendix](#appendix)


## Purpose
The REST API connects the [databases](https://github.com/satzbeleg/evidence-database) and the [web app](https://github.com/satzbeleg/evidence-app).

## Installation
Please follow the instruction of the [deployment repository](https://github.com/satzbeleg/evidence-deploy).


## Local Development
1. [Start local database and mail server](#start-local-database-and-mail-server)
2. [Install Ubuntu / Debian packages](#install-ubuntu--debian-packages)
3. [Install FastAPI in a separate virtual environment](#install-fastapi-in-a-separate-virtual-environment)
4. [Configure environment variables](#configure-environment-variables)
5. [Start the database container](#start-the-database-container)
6. [Start the FastAPI Server](#start-the-fastapi-server)

### Start local database and mail server

```bash
cd $EVIDENCE_DEPLOY 
docker-compose up --build dbauth dbeval mail
```

### Install Ubuntu / Debian packages

```bash
sudo apt update
sudo apt install -y --no-install-recommends build-essential python3-dev python3-venv
sudo apt install -y --no-install-recommends libpq-dev
```


### Install FastAPI in a separate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements-dev.txt
pip3 install -r requirements.txt
```


### Configure environment variables
In particular, the SMTP settings must be adapted.

```bash
cp dev.env .env
```


### Start the FastAPI Server

```bash
source .venv/bin/activate

uvicorn app.main:app \
   --host localhost --port 7070 \
   --reload --log-level debug
```

Open [http://localhost:7070/v1/docs](http://localhost:7070/v1/docs) in your browser.


## Check if the API is working


### (a) Add test email account directly in the database
In order to carry out the unit tests, a test account is created directly in the Postgres database. 
The test user has the email `nobody@example.com` and the password is `supersecret`.
**Never** do this on a production server!

```sh
export EVIDENCE_DEPLOY=../
(cd $EVIDENCE_DEPLOY && cat restapi/test/addtestaccount.sql | docker exec -i evidence_dbauth psql -U evidence -d evidence)
```

### (b) Run Unit Tests
```sh
cd restapi
source .venv/bin/activate
pytest
```

### (c) Login and get access token
Authenticate yourself with the test account. Request an access token.

```bash
EMAIL=nobody@example.com
PASSWORD=supersecret
curl -X POST "http://localhost:7070/v1/auth/login" \
    -H "accept: application/json" -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${EMAIL}&password=${PASSWORD}" \
    > mytokendata
cat mytokendata
TOKEN=$(cat mytokendata | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN
```

### (d) Save and load user settings

```bash
curl -X POST "http://localhost:7070/v1/user/settings" \
    -H  "accept: application/json" -H  "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" -d '{"hello":"world3"}'

curl -X POST "http://localhost:7070/v1/user/settings" \
    -H "accept: application/json" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" -d '{"test": 123}'

curl -X GET "http://localhost:7070/v1/user/settings" \
    -H  "accept: application/json" -H  "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}"
```

### (e) Sample BWS sets or training examples
```bash
curl -X GET "http://localhost:7070/v1/bestworst/random/4" \
    -H "accept: application/json" \
    -H "Authorization: Bearer ${TOKEN}"

curl -X POST "http://localhost:7070/v1/bestworst/samples/4/3/100/0" \
    -H  "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{"headword": "blau"}'

curl -X POST "http://localhost:7070/v1/interactivity/training-examples/5/10/0" \
    -H  "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{"headword": "blau"}'

curl -X POST "http://localhost:7070/v1/serialized-features" \
    -H  "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{"headword": "blau", "limit": 5}'

# model weights
curl -X POST "http://localhost:7070/v1/model/save" \
    -H  "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{"weights": [0.2, -0.3, 1.3, -0.4]}'

curl -X POST "http://localhost:7070/v1/model/load" \
    -H  "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" 

curl -X POST "http://localhost:7070/v1/model/load-all" \
    -H  "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" 
```


### (f) In Python

```python
import requests
data = {"username": "nobody@example.com", "password": "supersecret"}
resp = requests.post("http://localhost:7070/v1/auth/login", data)
print(resp.text)

TOKEN = resp.json()['access_token']
headers = {'Authorization': f"Bearer {TOKEN}"}

resp = requests.get("http://localhost:7070/v1/bestworst/random/5", headers=headers)
print(resp.json())
```


### (g) Similarity matrices

```sh
curl -X POST "http://localhost:7070/v1/variation/similarity-matrices" \
    -H  "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{"headword": "Internet", "limit": 50}'
```



## Authentication Process
The authentication mechanism is implemented in

- the [databases](https://github.com/satzbeleg/evidence-database) repository: `dbauth/
- the REST API repository: `app/routers/auth_email.py`

It is very important to setup the SMTP credentials to send verification emails.

### The Authentication Workflow
- In the UI, the user enters his email and desired password and sends it to the API
- API: Email / PW is forwarded to DB
- DB creates an inactive user account and returns verification token and API.
- API sends email with verification link to the specified email
- User clicks verification link
- API reads verification tokens and sends them to the DB
- DB checks verification token and sets user account to active.

### Create a new user account (register)
Please replace `you@example.com` with a valid email.

```sh
EMAIL=you@example.com
PASSWORD=secret2
curl -X POST "http://localhost:7070/v1/auth/register" \
    -H "accept: application/json" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${EMAIL}&password=${PASSWORD}"
```

### Process verification link (verify)
Please use the link in your email inbox.

```sh
VERIFYTOKEN=273950a0-a11a-461b-83b3-12ddd1b1d9b5
curl -X GET "http://localhost:7070/v1/auth/verify/${VERIFYTOKEN}"
```

#### Log in (login)

```bash
curl -X POST "http://localhost:7070/v1/auth/login" \
    -H "accept: application/json" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${EMAIL}&password=${PASSWORD}" > mytokendata
TOKEN=$(cat mytokendata | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN
```



## Appendix

### Documentation
- Show the docs: http://localhost:7070/v1/docs
- Show Redoc: http://localhost:7070/v1/redoc


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
You are asked to sign the CLA on your first pull request.
