# Sketelon App
Intended to be a simple baseline for python essentials

## Features
  - Config 
  - Logger
  - Database
  - Main with args

### Usage
Install dependancies from pyproject.toml:
  - run: ```pip install .```

Virtual Environment:
  - Create a venv: ```python -m venv .venv```
  - From the root directory run: ```source .venv/Scripts/activate```

Run Flask App:
  - From the 'src' directory run: ```flask --app flask_app run```
  - Go to "http://127.0.0.1:500" in a browser

Run a test:
  - From the 'src' directory run: ```python -m test.log_test```