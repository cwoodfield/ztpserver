#!/usr/bin/env python2.7

from flask import request
from app import app
import os

'''
(Hey everyone, if this logic doesn't belong in the routes.py file, 
let me know)

This is a dynamic configuration generator for ZTP clients. The 
general logic is as follows:

- On startup, load YAML file containing client data. Each client
  has a role, which in turn points to a template.
- When request comes into the endpoint, determine MAC (or IP?)
  from HTTP request, look up matching client, which points to a
  YAML path and role. Render matching template with facts from 
  the YAML file, then serve up the resulting configuration.
  
  * (I really should modularize this to accept other data sources)
'''

ZTP_BASEDIR = '/usr/local/etc/ztp/'
CLIENT_MAP_FILE = ZTP_BASEDIR + 'ztp_clients.yaml'


class ZTPCore(object):

  def __init__():
    self.clients = self.load_clients()    

  def load_clients():
    try:
      with open(CLIENT_MAP_FILE) as f:
        try:
          client_map = yaml.load(f)

        except yaml.YAMLError as e:
          sys.exit('Could not load YAML template {}: {}'.format(f, e)

    except IOError as e:
      sys.exit('Could not read file {}: {}'.format(template, e))

    '''
    Transform client structure into dict keyed by IP address
    If client has both IPv4 and IPv6, we'll just make two keys
    so either one on the request line will generate the right
    config.
    '''
    self.clients = {}
    for client in client_map['clients']
    if ip4_addr in client:
      self.clients[client['ip4_addr'] = client
    if ip6_addr in client:
      self.clients[client['ip6_addr'] = client

    roles = client_map['roles']
    self.templates = self.load_templates(roles)

  def _load_templates(self, roles):
    # Build dictionary of role name and matching template
    template_map = {}
    for name, template in roles.items():
      try:
        template_path = ZTP_BASEDIR + template
        with open(template_path) as f:
          template_map[name] = f.read()

      except IOError as e:
        sys.exit('Could not read file {}: {}'.format(template, e))

  def render(self, remote_addr):
    # Look up client IP, get template and load YAML
    

# Instantiate core class for future interactions
core = ZTPCore()

# From the tutorial. Remove if you care later, can be used to confirm flask
# functionality until then.
@app.route('/')
@app.route('/index')
def index():
  return "Hello, World!"

@app.route('/generate')
def generate():
  return core.render(request.remote_addr)
  

