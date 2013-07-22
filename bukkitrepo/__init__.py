from flask import Flask
import glob
import os
import json
import importlib

# Load config
config_json = open(os.path.dirname(__file__) + "/config/config.json", "r")
CONFIG = json.loads(config_json.read())

app = Flask(__name__)
app.secret_key = CONFIG['session_secret_key']

# Import routes
import bukkitrepo.routes

# Import views
module_names = [os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__) + "/views/*.py")]

for module in module_names:
    if module != '__init__':
        importlib.import_module('bukkitrepo.views.{0}'.format(module))
