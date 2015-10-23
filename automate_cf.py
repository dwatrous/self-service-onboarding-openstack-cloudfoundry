#-------------------------------------------------------------------------------
# Name:        automate_cf
# Purpose:     This module is designed to automated certain administrative
#              cloudfoundry operations using the cloudfoundry API and some
#              Stackato API functions
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

import os
import requests
import json
from attrdict import AttrDict
from string import Template

class cf_organization:
    def __init__(self, organization):
        self.guid = organization['metadata']['guid']
        # TODO: use https://docs.python.org/2/library/time.html#time.strptime to make these time values
        self.created = organization['metadata']['created_at']
        self.updated = organization['metadata']['updated_at']
        self.billing_enabled = organization['entity']['billing_enabled']
        self.is_default = organization['entity']['is_default']
        self.name = organization['entity']['name']
        self.quota_definition_guid = organization['entity']['quota_definition_guid']
        self.status = organization['entity']['status']

class cf_user:
    def __init__(self, user):
        self.guid = user['metadata']['guid']
        # TODO: use https://docs.python.org/2/library/time.html#time.strptime to make these time values
        self.created = user['metadata']['created_at']
        self.updated = user['metadata']['updated_at']
        self.logged_in = user['metadata']['logged_in_at']
        self.active = user['entity']['active']
        self.admin = user['entity']['admin']
        self.default_space_guid = user['entity']['default_space_guid']
        self.username = user['entity']['username']

class cf_quota:
    def __init__(self, quota):
        self.guid = quota['metadata']['guid']
        # TODO: use https://docs.python.org/2/library/time.html#time.strptime to make these time values
        self.created = quota['metadata']['created_at']
        self.updated = quota['metadata']['updated_at']
        self.name = quota['entity']['name']
        self.allow_sudo = quota['entity']['allow_sudo']
        self.memory_limit = quota['entity']['memory_limit']
        self.instance_memory_limit = quota['entity']['instance_memory_limit']
        self.non_basic_services_allowed = quota['entity']['non_basic_services_allowed']
        self.total_droplets = quota['entity']['total_droplets']
        self.total_routes = quota['entity']['total_routes']
        self.total_services = quota['entity']['total_services']
        self.trial_db_allowed = quota['entity']['trial_db_allowed']

class cf_space:
    def __init__(self, space):
        self.is_default = space['entity']['is_default']
        self.name = space['entity']['name']
        self.space_quota_definition_guid = space['entity']['space_quota_definition_guid']
        self.created_at = space['metadata']['created_at']
        self.guid = space['metadata']['guid']
        self.updated_at = space['metadata']['updated_at']

class automate_cf:

    # URL templates
    url_auth_request        = Template('https://$authhost/uaa/oauth/token')
    url_get_info            = Template('https://$apihost/info')
    url_organization        = Template('https://$apihost/v2/organizations')
    url_organization_by_guid = Template('https://$apihost/v2/organizations/$guid')
    url_organization_managers_by_guid = Template('https://$apihost/v2/organizations/$guid/managers')
    url_find_organization_by_name = Template('https://$apihost/v2/organizations?q=name:$orgname')
    url_get_organization_for_user = Template('https://$apihost/v2/users/$userguid/organizations')
    url_get_organizations_managed_by_user = Template('https://$apihost/v2/users/$userguid/managed_organizations')
    url_space               = Template('https://$apihost/v2/spaces')
    url_get_users           = Template('https://$apihost/v2/users?limit=$limit')
    url_find_user_by_username = Template('https://$apihost/v2/users?q=username:$useremail')
    url_get_users_by_org    = Template('https://$apihost/v2/organizations/$organization/users')
    url_create_user         = Template('https://$apihost/v2/stackato/users')    # Stackato specific call
    url_add_user_organization = Template('https://$apihost/v2/organizations/$organization/users/$user')
    url_make_user_manager   = Template('https://$apihost/v2/organizations/$organization/managers/$user')
    url_get_quotas          = Template('https://$apihost/v2/quota_definitions')
    url_find_quotas_by_name = Template('https://$apihost/v2/quota_definitions?q=name:$quotaname')

    def __init__(self):
        # load in configuration
        path_to_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'als.conf.json')
        self.configuration = json.load(open(path_to_conf, 'r'))
        # choose sensible defaults if the conf file hasn't been updated by ansible
        if self.configuration['auth_host'] == "{{ cf_auth_host }}":
            self.configuration['auth_host'] = "aok.als-dev.hos.hpecorp.net"
        if self.configuration['api_host'] == "{{ cf_api_host }}":
            self.configuration['api_host'] = "api.als-dev.hos.hpecorp.net"

    ## Authentication functions
    def load_access_token(self):
        url = self.url_auth_request.substitute(authhost=self.configuration['auth_host'])
        headers = {'AUTHORIZATION': 'Basic Y2Y6'}
        data = {'username': self.configuration['automation_username'], 'password': self.configuration['automation_password'], 'grant_type': 'password'}
        response = requests.post(url, headers=headers, data=data, verify=self.configuration['verify_ssl'])
        self.oauth = AttrDict(json.loads(response.text))

    def get_access_token(self):
        # if oauth isn't set the request a new access token
        if not hasattr(self, 'oauth') or not hasattr(self.oauth, 'access_token'):
            self.load_access_token()
        # verify that the access token is still valid, else renew
        url = self.url_organization.substitute(apihost=self.configuration['api_host'])
        response = requests.get(url, headers={'AUTHORIZATION': 'bearer ' + self.oauth.access_token}, verify=self.configuration['verify_ssl'])
        if response.status_code != 200:
            delattr(self, 'oauth')
            self.load_access_token()
        # return the access_token
        return self.oauth.access_token

    def add_auth_header(self, headers={}):
        headers.update({'AUTHORIZATION': 'bearer ' + self.get_access_token()})
        return headers

    ## Standard API requests and searches
    def call_api(self, url, headers={}):
        response = requests.get(url, headers=self.add_auth_header(headers), verify=self.configuration['verify_ssl'])
        if response.status_code in [200]:
            parsed_response = json.loads(response.text)
            if 'resources' in parsed_response:
                return parsed_response['resources']
            else:
                return parsed_response
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

    def get_info(self):
        url = self.url_get_info.substitute(apihost=self.configuration['api_host'])
        return self.call_api(url)

    def get_organizations(self):
        organizations = []
        url = self.url_organization.substitute(apihost=self.configuration['api_host'])
        organizations_response = self.call_api(url)
        for organization in organizations_response:
            organizations.append(cf_organization(organization))
        return organizations

    def get_organizations_for_user(self, userguid):
        organizations = []
        url = self.url_get_organization_for_user.substitute(apihost=self.configuration['api_host'], userguid=userguid)
        organizations_response = self.call_api(url)
        for organization in organizations_response:
            organizations.append(cf_organization(organization))
        return organizations

    def get_organizations_managed_by_user(self, userguid):
        organizations = []
        url = self.url_get_organizations_managed_by_user.substitute(apihost=self.configuration['api_host'], userguid=userguid)
        organizations_response = self.call_api(url)
        for organization in organizations_response:
            organizations.append(cf_organization(organization))
        return organizations

    def get_organizations_by_guid(self, organization_guid):
        organizations = []
        url = self.url_organization_by_guid.substitute(apihost=self.configuration['api_host'], guid=organization_guid)
        organizations_response = self.call_api(url)
        for organization in organizations_response:
            organizations.append(cf_organization(organization))
        return organizations

    def get_organization_managers_by_guid(self, organization_guid):
        organizations = []
        url = self.url_organization_managers_by_guid.substitute(apihost=self.configuration['api_host'], guid=organization_guid)
        organizations_response = self.call_api(url)
        for organization in organizations_response:
            organizations.append(cf_user(organization))
        return organizations

    def find_organizations_by_name(self, name):
        organizations = []
        url = self.url_find_organization_by_name.substitute(apihost=self.configuration['api_host'], orgname=name)
        organizations_response = self.call_api(url)
        for organization in organizations_response:
            organizations.append(cf_organization(organization))
        return organizations

    def get_users(self):
        # TODO handle pagination better than really big magic numbers
        limit = 1000
        users = []
        url = self.url_get_users.substitute(apihost=self.configuration['api_host'], limit=limit)
        users_response = self.call_api(url)
        # convert raw response into cf_user objects and add to users
        for user in users_response:
            users.append(cf_user(user))
        return users

    def find_user_by_username(self, username):
        url = self.url_find_user_by_username.substitute(apihost=self.configuration['api_host'], useremail=username)
        users_response = self.call_api(url)
        if len(users_response) > 1:
            raise Exception({'status': 300, 'message': 'The username provided matches multiple users. Please be more specific.'})
        # convert raw response into cf_user objects and return
        return cf_user(users_response[0])

    def get_users_for_organization(self, org_guid):
        users = []
        url = self.url_get_users_by_org.substitute(apihost=self.configuration['api_host'], organization=org_guid)
        users_response = self.call_api(url)
        # convert raw response into cf_user objects and add to users
        for user in users_response:
            users.append(cf_user(user))
        return users

    def get_quotas(self):
        quotas = []
        url = self.url_get_quotas.substitute(apihost=self.configuration['api_host'])
        quotas_response = self.call_api(url)
        # convert raw response into cf_quota objects and add to quotas
        for quota in quotas_response:
            quotas.append(cf_quota(quota))
        return quotas

    def find_quota_by_name(self, quota_name):
        url = self.url_find_quotas_by_name.substitute(apihost=self.configuration['api_host'], quotaname=quota_name)
        quota = self.call_api(url)
        if len(quota) > 1:
            raise Exception({'status': 300, 'message': 'The quota name provided matches multiple quotas. Please be more specific.'})
        return cf_quota(quota[0])

    ## API creation functions
    def create_organization(self, name):
        default_quota_guid = self.find_quota_by_name('default').guid
        url = self.url_organization.substitute(apihost=self.configuration['api_host'])
        data = {'name':name, 'billing_enabled':False, 'quotadefinitionguid':default_quota_guid, 'domain_guids':[], 'user_guids':[], 'manager_guids':[], 'billingmanagerguids':[], 'auditor_guids':[]}
        response = requests.post(url, headers=self.add_auth_header(), json=data, verify=self.configuration['verify_ssl'])
        if response.status_code in [200,201]:
            return cf_organization(json.loads(response.text))
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

    def create_space(self, name, organization_guid):
        url = self.url_space.substitute(apihost=self.configuration['api_host'])
        data = {"name": name,"organization_guid": organization_guid,"developer_guids":[],"manager_guids":[],"auditor_guids":[],"app_guids":[],"domain_guids":[],"serviceinstanceguids":[]}
        response = requests.post(url, headers=self.add_auth_header(), json=data, verify=self.configuration['verify_ssl'])
        if response.status_code in [200,201]:
            return cf_space(json.loads(response.text))
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

    def create_user(self, email):
        url = self.url_create_user.substitute(apihost=self.configuration['api_host'])
        data = {"admin": False, "email": email, "password":"secret", "username": email}
        response = requests.post(url, headers=self.add_auth_header(), json=data, verify=self.configuration['verify_ssl'])
        if response.status_code in [200,201]:
            return cf_user(json.loads(response.text))
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

    def add_user_to_organization(self, user_guid, organization_guid):
        url = self.url_add_user_organization.substitute(apihost=self.configuration['api_host'], user=user_guid, organization=organization_guid)
        response = requests.put(url, headers=self.add_auth_header(), verify=self.configuration['verify_ssl'])
        if response.status_code in [200,201]:
            return cf_organization(json.loads(response.text))
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

    def remove_user_from_organization(self, user_guid, organization_guid):
        url = self.url_add_user_organization.substitute(apihost=self.configuration['api_host'], user=user_guid, organization=organization_guid)
        response = requests.delete(url, headers=self.add_auth_header(), verify=self.configuration['verify_ssl'])
        if response.status_code in [200,201]:
            return cf_organization(json.loads(response.text))
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

    def make_user_manager(self, user_guid, organization_guid):
        url = self.url_make_user_manager.substitute(apihost=self.configuration['api_host'], user=user_guid, organization=organization_guid)
        response = requests.put(url, headers=self.add_auth_header(), verify=self.configuration['verify_ssl'])
        if response.status_code in [200,201]:
            return cf_organization(json.loads(response.text))
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})

    def remove_user_manager(self, user_guid, organization_guid):
        url = self.url_make_user_manager.substitute(apihost=self.configuration['api_host'], user=user_guid, organization=organization_guid)
        response = requests.delete(url, headers=self.add_auth_header(), verify=self.configuration['verify_ssl'])
        if response.status_code in [200,201]:
            return cf_organization(json.loads(response.text))
        else:
            raise Exception({'status': response.status_code, 'message': json.loads(response.text)})


def main():
    alsauto = automate_als();

    # some example usage
    quota = alsauto.find_quota_by_name('default')
    org = alsauto.find_organizations_by_name('default')
    users = alsauto.get_users()
    oneuser = alsauto.find_user_by_username('user@domain.com')
    user_managed_organizations = alsauto.get_organizations_managed_by_user(users[0].guid)
    org_users = alsauto.get_users_for_organization(org[0].guid)

    # example to create new org, space, user...
    new_org = alsauto.create_organization('Test Python Stuff 2')
    new_space = alsauto.create_space('Test space', new_org.guid)
    new_user = alsauto.create_user('test.user@hp.com')
    associate_user = alsauto.add_user_to_organization(new_user.guid, new_org.guid)
    manager_user = alsauto.make_user_manager(new_user.guid, new_org.guid)
    remove_user = alsauto.remove_user_from_organization(new_user.guid, new_org.guid)

if __name__ == '__main__':
    main()
