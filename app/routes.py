#!/usr/bin/env python2.7

from flask import request
from app import app
from core import ZTPCore
from exceptions import *


ZTP_BASEDIR = '/usr/local/etc/ztp/'
CLIENT_MAP_FILE = 'ztp_clients.yaml'


# Instantiate core class for future interactions
core = ZTPCore(ZTP_BASEDIR, CLIENT_MAP_FILE)

# From the tutorial. Remove if you care later, can be used to confirm flask
# functionality until then.
@app.route('/')
@app.route('/index')
def index():
  return "Hello, World!"

# Generate config for client
@app.route('/generate')
def generate():
  try:
    # Check for ?client= in query string, use this first (overrides the actual client IP)
    if 'client' in request.args:
      config = core.render(request.args['client'])
    else:
      config = core.render(request.remote_addr)
  
  except ZTPClientNotFoundError as e:
    return ("Client Not Found", 404)

  except ZTPRenderingError as e:
    return (e, 503)

  return config
  

