FROM debian:buster-slim AS base

# install python
RUN apt-get update
RUN apt-get install -y --no-install-recommends python3
RUN apt-get clean && rm -rf /var/lib/apt/lists/*


# ------------- Part 1 -------------
FROM base AS builder

# install build dependencies
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential python3-dev python3-venv
RUN apt-get install -y --no-install-recommends libpq-dev

# install virtual env
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# install packages
RUN pip3 install --no-cache-dir --upgrade pip
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# compile to bytecode
RUN python3 -O -m compileall $VIRTUAL_ENV

# remove build dependencies
RUN apt-get remove --purge --auto-remove -y build-essential python3-dev python3-venv
RUN apt-get clean && rm -rf /var/lib/apt/lists/*


# ------------- Part 2 -------------
FROM base 

ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Port Setting
EXPOSE 80

# Copy /app/main.py
COPY ./app /app

# Start server (enable if container startup is NOT configured in restapi.yml)
#CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:80", "--worker-class", "uvicorn.workers.UvicornH11Worker", "--workers", "2", "--worker-tmp-dir", "/dev/shm"]
