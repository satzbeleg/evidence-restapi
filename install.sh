#!/bin/bash

# install virtual env
python3 -m venv .venv

# start virtual env
source .venv/bin/activate

# install packages
pip3 install --upgrade pip
pip3 install -r requirements-local.txt
pip3 install -r requirements.txt

# create temporary folder for downloads
#mkdir -p .tmp
