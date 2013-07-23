from flask import Flask
import os
import json

# Load config
config_json = open(os.path.dirname(__file__) + "/config/config.json", "r")
CONFIG = json.loads(config_json.read())

app = Flask(__name__)
app.secret_key = CONFIG['session_secret_key']

# Import routes
import bukkitrepo.routes
