import sys
import random
import string
import os
import json


def fail():
    print("fail")
    sys.exit(1)


def ok():
    print("ok")


print("Welcome to the Bukkit Repo configuration tool. I'll help you configure Bukkit Repo for initial setup. Please note that this program will overwrite any existing configuration, so please exit now if you do not want this to happen.\n")
print("The first thing I'm going to check is whether you have the required Python modules installed.\n")

sys.stdout.write("Checking for Python 3.3 or higher...")

if sys.version_info[0] == 3 and sys.version_info[1] >= 3:
    ok()
else:
    fail()

sys.stdout.write("Checking for flask...")

try:
    import flask
except ImportError:
    fail()

ok()

sys.stdout.write("Checking for requests...")

try:
    import requests
except ImportError:
    fail()

ok()

sys.stdout.write("Checking for pymongo...")

try:
    import pymongo
except ImportError:
    fail()

ok()

sys.stdout.write("Checking for passlib...")

try:
    import passlib
except ImportError:
    fail()

ok()

print()
print("All of the requirement tests have passed. The last step is to write the configuration file.")

config = {'database': {}}

config['recaptcha_private_key'] = input("What is the recaptcha private key? ")
config['mandrill_api_key'] = input("What is the mandrill API key? ")
generate_session_key = input('Bukkit Repo uses a private "session key" in order to encrypt user data. Do you want me to generate one for you? [yes/no] ')

if generate_session_key.lower() == 'yes' or generate_session_key.lower() == 'y':
    config['session_secret_key'] = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32))
else:
    config['session_secret_key'] = input('What session key should I use? ')

config['database']['host'] = input('What host is the mongodb database server located on? ')
config['database']['port'] = input('What port is the mongodb database server located on? ')
config['database']['db'] = input('What database should I use on the database server? ')

print()
print("Writing to file...")

config_file_path = os.path.dirname(__file__) + 'bukkitrepo/config/config.json'

try:
    os.remove(config_file_path)
except OSError:
    pass

config_file = open(config_file_path, 'wb')
config_json = json.dumps(config)
config_file.write(bytes(config_json, 'UTF-8'))
config_file.close()
