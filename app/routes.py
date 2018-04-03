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

def remote_addr(request):
  if 'client' in request.args:
    return request.args['client']
  else:
    return request.remote_addr


@app.route('/')
@app.route('/index')
def index():
  return "Hello, World!"


# Generate config for client
@app.route('/generate')
def generate():
  client_addr = remote_addr(request)

  try:
    return core.render(client_addr)
  
  except ZTPClientNotFoundError as e:
    return ('Client Not Found', 404)

  except ZTPRenderingError as e:
    return (e, 503)


# Serve bootstrap script
@app.route('/bootstrap')
def bootstrap():
  client_addr = remote_addr(request)

  try:
    return core.bootstrap(client_addr)
  except ZTPError as e:
    return ('Bootstrap file not found', 404)


# Serve software image
@app.route('/software')
def software():
  client_addr = remote_addr(request)

  try:
    return core.software(client_addr)
  
  except ZTPError as e:
    return ('Software image not found', 404)
