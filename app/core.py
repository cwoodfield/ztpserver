#!/usr/bin/env python2.7

from jinja2 import Environment, BaseLoader
import yaml
from app import app
import os
import sys
import pdb
from exceptions import *

'''
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


class ZTPCore(object):

  def __init__(self, ztp_basedir, client_file):
    '''
    init method does the following:
    - Populates basedir attribute
    - Reads client map file
    - Builds dicts:
      self.clients - keyed on client IP
      self.roles - keyed on role name
      self.templates - j2 templates keyed on role name
    '''

    # Add dir path to basedir, will save us from
    # having to do this every time later
    if ztp_basedir[-1] != '/':
      ztp_basedir = ztp_basedir + '/'

    self.ztp_basedir = ztp_basedir
    self.client_path = ztp_basedir + client_file

    try:
      with open(self.client_path) as f:
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
    try:
      for client in client_map['clients']:
        if 'ip4_addr' in client:
          self.clients[client['ip4_addr']] = client
        if 'ip6_addr' in client:
          self.clients[client['ip6_addr']] = client

      self.roles = {}
      for role in client_map['roles']:
        if 'name' in role:
          self.roles[role['name']] = role

    except KeyError:
      sys.exit('No \'{}\' key found in client configuration file.'.format(e))

    # Preload j2 templates
    self.templates = self._load_templates(self.roles)

  def _load_templates(self, roles):
    # Build dictionary of role name and matching template
    template_map = {}
    for role in roles.values():
      try:
        name = role['name']
        template_path = self.ztp_basedir + role['template_file']
        with open(template_path) as f:
          template_map[name] = f.read()

      except IOError as e:
        sys.exit('Could not read file {}: {}'.format(template, e))

      except KeyError as e:
        sys.exit('Malformed YAML, missing \'name\' or \'template_path\' keys in role: {}'.format(e))

    return template_map

  def _role_lookup(self, remote_addr):
    # Return role dict based on client lookup
    try:
      client = self.clients[remote_addr]

    except KeyError as e:
      raise ZTPClientNotFoundError('Client IP Address is not recognized.')

    # Get role data
    try:
      return self.roles[client['role']]

    except KeyError as e:
      raise ZTPMalformedClientException('Could not load role {}'.format([client['role']]))

  def render(self, remote_addr):
    # Look up client IP, get template and load YAML
    try:
      client = self.clients[remote_addr]
    except KeyError as e:
      raise ZTPClientNotFoundError('Client IP Address is not recognized.')

    # Can we load the YAML data?
    try:
      yaml_path = self.ztp_basedir + client['facts_file']
      template = self.templates[self._role_lookup(remote_addr)['name']]
    except KeyError as e:
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

  def bootstrap(self, remote_addr):

    #pdb.set_trace()
    # Look up bootstrap script file from role
    role_data = self._role_lookup(remote_addr)

    try:
      bootstrap_path = self.ztp_basedir + role_data['bootstrap_file']
      with open(bootstrap_path, 'rb') as f:
        bootstrap_file = f.read()

      return bootstrap_file

    except KeyError as e:
      raise ZTPError('Role \'{}\'does not contain bootstrap file'.format(role_data['name']))

    except IOError as e:
      raise ZTPError('Error reading bootstrap file: {}'.format(e))

  def software(self, remote_addr):

    #pdb.set_trace()
    # Look up bootstrap script file from role
    role_data = self._role_lookup(remote_addr)

    try:
      software_path = self.ztp_basedir + role_data['software_file']
      with open(software_path, 'rb') as f:
        software_file = f.read()

      return software_file
    
    except KeyError as e:
      raise ZTPError('Role \'{}\'does not contain software file'.format(role_data['name']))

    except IOError as e:
      raise ZTPError('Error reading software file: {}'.format(e))

