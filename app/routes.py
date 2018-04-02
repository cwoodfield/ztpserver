#!/usr/bin/env python2.7

from flask import request
from jinja2 import Environment, BaseLoader
import yaml
from app import app
import os
import sys
import pdb
from exceptions import *

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

  def __init__(self):
    try:
      with open(CLIENT_MAP_FILE) as f:
        try:
          client_map = yaml.load(f)

        except yaml.YAMLError as e:
          sys.exit('Could not load YAML template {}: {}'.format(f, e))

    except IOError as e:
      sys.exit('Could not read file {}: {}'.format(template, e))

    '''
    Transform client structure into dict keyed by IP address
    If client has both IPv4 and IPv6, we'll just make two keys
    so either one on the request line will generate the right
    config.
    '''
    self.clients = {}
    for client in client_map['clients']:
      if 'ip4_addr' in client:
        self.clients[client['ip4_addr']] = client
      if 'ip6_addr' in client:
        self.clients[client['ip6_addr']] = client

    try:
      roles = client_map['roles']

    except KeyError:
      sys.exit('No \'roles\' key found in configuration file.')

    self.templates = self._load_templates(roles)

    #pdb.set_trace()

  def _load_templates(self, roles):
    # Build dictionary of role name and matching template
    template_map = {}
    #pdb.set_trace()
    for role in roles:
      try:
        name = role['name']
        template_path = ZTP_BASEDIR + role['template_name']
        with open(template_path) as f:
          template_map[name] = f.read()

      except IOError as e:
        sys.exit('Could not read file {}: {}'.format(template, e))

      except KeyError as e:
        sys.exit('Malformed YAML, missing \'name\' or \'template_path\' keys in role: {}'.format(e))

    return template_map

  def render(self, remote_addr):
    #pdb.set_trace()
    # Look up client IP, get template and load YAML
    try:
      client = self.clients[remote_addr]
    except KeyError:
      raise ZTPClientNotFoundError('Client IP Address is not recognized.')

    # Can we load the YAML data?
    try:
      yaml_path = ZTP_BASEDIR + client['facts_file']
      template = self.templates[client['role']]
    except KeyError:
      raise ZTPMalformedClientRecordException('Could not find role or facts file.')

    # Load facts YAML file
    try:
      with open(yaml_path) as f:
        context = yaml.load(f)
        
      env_template = Environment(loader=BaseLoader).from_string(template)
      config = env_template.render(context)  

      return config

    except IOError as e:
      raise ZTPRenderingError('Could not load facts file for host {}" {}'.format(client['name'], e))

    except yaml.YAMLError as e:
      raise ZTPRenderingError('Could not load facts file for host {}: {}'.format(client['name'], e))

    except jinja2.TemplateError as e:
      raise ZTPRenderingError('Could not render template for host {}: {}'.format(client['name'], e))


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
  try:
    # Check for ?client in query string, use this first (for testing)
    if 'client' in request.args:
      config = core.render(request.args['client'])
    else:
      config = core.render(request.remote_addr)
  
  except ZTPClientNotFoundError as e:
    return ("Client Not Found", 404)

  except ZTPRenderingError as e:
    return (e, 503)

  return config
  

