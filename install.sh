#!/bin/bash

# install virtual env
python3.6 -m venv .venv

# start virtual env
source .venv/bin/activate

# install packages
pip3 install --upgrade pip
pip3 install -r requirements-server.txt
pip3 install -r requirements-dev.txt
pip3 install -r requirements.txt

# create temporary folder for downloads
#mkdir -p .tmp
