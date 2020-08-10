#!/bin/bash

# delete  `.pyc` files: 
find . -type f -name "*.pyc" | xargs rm

# delete `__pycache__` folders 
find . -type d -name "__pycache__" | xargs rm -r

# delete `.pytest_cache` folder
rm -r .pytest_cache

# delete virtual env
rm -r .venv
