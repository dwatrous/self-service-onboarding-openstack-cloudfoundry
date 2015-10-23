#-------------------------------------------------------------------------------
# Name:        automate_openstack
# Purpose:
#
# Author:      Daniel Watrous
#
# Created:     05/05/2015
# Copyright (c) 2015 Hewlett Packard Enterprise
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

#https://pypi.python.org/pypi/python-keystoneclient/1.3.1
import os
import requests
import json
from attrdict import AttrDict
from string import Template

class automate_openstack_v3:

    # load in configuration
    path_to_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openstack.v3.conf.json')
    configuration = json.load(open(path_to_conf, 'r'))

    url_auth_request        = Template('https://$identityhost/v3/auth/tokens')
    url_projects            = Template('https://$identityhost/v3/projects')

    def __init__(self):
        self.load_access_token();

    ## Authentication functions
    def load_access_token(self):
        url = self.url_auth_request.substitute(identityhost=self.configuration['identity_host'])
        headers = {'Accept': 'application/json'}
        data = {"auth":
                    {"identity":
                        {"methods": ["password"], "password": {"user": {"domain": {"name": self.configuration['user_domain_name']}, "name": self.configuration['username'], "password": self.configuration['password']}}}
                    }
                }
        response = requests.post(url, headers=headers, json=data, verify=self.configuration['verify_ssl'])
        self.token = response.headers.get('x-subject-token')

    def add_auth_header(self, headers={}):
        # TODO: catch case where access_token is not set or is invalid
        headers.update({'X-Auth-Token': self.token})
        return headers

    def get_project_list(self):
        url = self.url_projects.substitute(identityhost=self.configuration['identity_host_adm'])
        response = requests.get(url, headers=self.add_auth_header(), verify=self.configuration['verify_ssl'])
        if response.status_code in [200]:
            parsed_response = json.loads(response.text)
            if 'tenants' in parsed_response:
                return parsed_response['tenants']
            else:
                return parsed_response
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

class automate_openstack_v2:

    # load in configuration
    path_to_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'openstack.v2.conf.json')
    configuration = json.load(open(path_to_conf, 'r'))

    url_auth_request        = Template('https://$identityhost/v2.0/tokens')
    url_tenants             = Template('https://$identityhost/v2.0/tenants')
    url_servers_for_tenant  = Template('https://$computehost/v2/$tenant_id/servers')

    def __init__(self):
        self.load_access_token();

    ## Authentication functions
    def load_access_token(self):
        url = self.url_auth_request.substitute(identityhost=self.configuration['identity_host'])
        headers = {'Content-Type': 'application/json'}
        data = {"auth": {"tenantName": self.configuration['tenant'], "passwordCredentials": {"username": self.configuration['username'], "password": self.configuration['password']}}}
        response = requests.post(url, headers=headers, json=data, verify=self.configuration['verify_ssl'])
        token_response = json.loads(response.text)
        self.token = AttrDict(token_response['access']['token'])

    def add_auth_header(self, headers={}):
        # TODO: catch case where access_token is not set or is invalid
        headers.update({'X-Auth-Token': self.token.id})
        return headers

    def get_project_list(self):
        url = self.url_tenants.substitute(identityhost=self.configuration['identity_host_adm'])
        response = requests.get(url, headers=self.add_auth_header(), verify=self.configuration['verify_ssl'])
        if response.status_code in [200]:
            parsed_response = json.loads(response.text)
            if 'tenants' in parsed_response:
                return parsed_response['tenants']
            else:
                return parsed_response
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

    def get_servers_for_tenant(self, tenant_id):
        url = self.url_servers_for_tenant.substitute(computehost=self.configuration['nova_host'], tenant_id=tenant_id)
        response = requests.get(url, headers=self.add_auth_header(), verify=self.configuration['verify_ssl'])
        if response.status_code in [200]:
            parsed_response = json.loads(response.text)
            if 'tenants' in parsed_response:
                return parsed_response['tenants']
            else:
                return parsed_response
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

def main():
##    print '***** project list using keystone v3 *****'
##    hosautov3 = automate_openstack_v3()
##    print hosautov3.get_project_list()

    print '***** project list using keystone v2 *****'
    hosautov2 = automate_openstack_v2()
    projects = hosautov2.get_project_list()
    for project in projects:
        try:
            servers_for_tenant = hosautov2.get_servers_for_tenant(project['id'])
            print servers_for_tenant
        except:
            print "Failed for " + project['name']


if __name__ == '__main__':
    main()
