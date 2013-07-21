from flask import Flask
import glob
import os
import json

# Load config
config_json = open(os.path.dirname(__file__) + "/config/config.json")
CONFIG = json.loads(config_json)

app = Flask(__name__)
app.secret_key = SESSION_SECRET_KEY

# Import routes
import bukkitrepo.routes

# Import views
module_names = [os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__) + "/views/*.py")]

for module in module_names:
    if module != '__init__':
        __import__('bukkitrepo.views.{0}'.format(module))
