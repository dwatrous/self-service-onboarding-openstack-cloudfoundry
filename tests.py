#-------------------------------------------------------------------------------
# Name:        tests for automation classes
# Purpose:
#
# Author:      Daniel Watrous
#
# Created:     06/23/2015
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

import mock
import unittest
import automate_cf
import automate_openstack

import requests
import httpretty
import json

class TestAutomateALS(unittest.TestCase):

    cf_quota_response = {'entity': {'allow_sudo': False,'instance_memory_limit': -1,'memory_limit': 12800,'name': 'default','non_basic_services_allowed': True,'total_droplets': 200,'total_routes': 10000,'total_services': 1000,'trial_db_allowed': False},'metadata': {'created_at': '2015-03-03T13:48:37-08:00','guid': '65100aba-2c20-4b94-b57f-19d43e219faf','updated_at': '2015-04-22T20:18:57-07:00','url': '/v2/quota_definitions/65100aba-2c20-4b94-b57f-19d43e219faf'}}
    cf_organization_response = {'entity': {'app_events_url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/app_events','auditors_url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/auditors','billing_enabled': False,'billing_managers_url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/billing_managers','domains_url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/domains','is_default': False,'managers_url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/managers','name': 'default','private_domains_url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/private_domains','quota_definition_guid': '65100aba-2c20-4b94-b57f-19d43e219faf','quota_definition_url': '/v2/quota_definitions/65100aba-2c20-4b94-b57f-19d43e219faf','space_quota_definitions_url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/space_quota_definitions','spaces_url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/spaces','status': 'active','users_url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/users'},'metadata': {'created_at': '2015-04-22T17:02:35-07:00','guid': '314b941b-11e6-4cb6-a441-67798d35a189','updated_at': None,'url': '/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189'}}
    cf_user_response = {u'entity': {u'active': True,u'admin': True,u'audited_organizations_url': u'/v2/users/d5c88a2c-01a1-49d0-b88c-6bfed012335a/audited_organizations',u'audited_spaces_url': u'/v2/users/d5c88a2c-01a1-49d0-b88c-6bfed012335a/audited_spaces',u'billing_managed_organizations_url': u'/v2/users/d5c88a2c-01a1-49d0-b88c-6bfed012335a/billing_managed_organizations',u'default_space_guid': None,u'guid': u'd5c88a2c-01a1-49d0-b88c-6bfed012335a',u'managed_organizations_url': u'/v2/users/d5c88a2c-01a1-49d0-b88c-6bfed012335a/managed_organizations',u'managed_spaces_url': u'/v2/users/d5c88a2c-01a1-49d0-b88c-6bfed012335a/managed_spaces',u'organizations_url': u'/v2/users/d5c88a2c-01a1-49d0-b88c-6bfed012335a/organizations',u'spaces_url': u'/v2/users/d5c88a2c-01a1-49d0-b88c-6bfed012335a/spaces',u'username': u'alsautomation'},u'metadata': {u'created_at': u'2015-05-07T15:41:19-07:00',u'guid': u'd5c88a2c-01a1-49d0-b88c-6bfed012335a',u'logged_in_at': u'2015-07-21T10:45:41-07:00',u'updated_at': u'2015-07-21T10:45:46-07:00',u'url': u'/v2/users/d5c88a2c-01a1-49d0-b88c-6bfed012335a'}}
    cf_organizations_managed_by_user_response = [{u'entity': {u'app_events_url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/app_events',u'auditors_url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/auditors',u'billing_enabled': False,u'billing_managers_url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/billing_managers',u'domains_url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/domains',u'is_default': False,u'managers_url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/managers',u'name': u'default',u'private_domains_url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/private_domains',u'quota_definition_guid': u'65100aba-2c20-4b94-b57f-19d43e219faf',u'quota_definition_url': u'/v2/quota_definitions/65100aba-2c20-4b94-b57f-19d43e219faf',u'space_quota_definitions_url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/space_quota_definitions',u'spaces_url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/spaces',u'status': u'active',u'users_url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189/users'},u'metadata': {u'created_at': u'2015-04-22T17:02:35-07:00',u'guid': u'314b941b-11e6-4cb6-a441-67798d35a189',u'updated_at': None,u'url': u'/v2/organizations/314b941b-11e6-4cb6-a441-67798d35a189'}},{u'entity': {u'app_events_url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d/app_events',u'auditors_url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d/auditors',u'billing_enabled': False,u'billing_managers_url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d/billing_managers',u'domains_url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d/domains',u'is_default': False,u'managers_url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d/managers',u'name': u'Test Python Stuff',u'private_domains_url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d/private_domains',u'quota_definition_guid': u'65100aba-2c20-4b94-b57f-19d43e219faf',u'quota_definition_url': u'/v2/quota_definitions/65100aba-2c20-4b94-b57f-19d43e219faf',u'space_quota_definitions_url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d/space_quota_definitions',u'spaces_url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d/spaces',u'status': u'active',u'users_url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d/users'},u'metadata': {u'created_at': u'2015-05-14T21:00:25-07:00',u'guid': u'72a8af68-313e-4233-99de-72fbaad4953d',u'updated_at': None,u'url': u'/v2/organizations/72a8af68-313e-4233-99de-72fbaad4953d'}}]

    def setUp(self):
        #setup the mock patcher for get_access_token
        get_access_token_patcher = mock.patch('automate_cf.automate_cf.get_access_token')
        self.addCleanup(get_access_token_patcher.stop)
        self.mock_get_access_token = get_access_token_patcher.start()
        self.mock_get_access_token.return_value = self.patcher_get_access_token()

        # create an automate_cf instance
        self.autoals = automate_cf.automate_cf()

    def patcher_get_access_token(self, **attrs):
        return 'MOCKTOKEN'

    def test_convert_response_cf_quota(self):
        quota = automate_cf.cf_quota(self.cf_quota_response)
        self.assertIsInstance(quota, automate_cf.cf_quota)
        self.assertEqual(quota.memory_limit, self.cf_quota_response['entity']['memory_limit'])
        self.assertEqual(quota.name, self.cf_quota_response['entity']['name'])
        self.assertEqual(quota.guid, self.cf_quota_response['metadata']['guid'])

    def test_convert_response_cf_organization(self):
        organization = automate_cf.cf_organization(self.cf_organization_response)
        self.assertIsInstance(organization, automate_cf.cf_organization)
        self.assertEqual(organization.guid, self.cf_organization_response['metadata']['guid'])
        self.assertEqual(organization.name, self.cf_organization_response['entity']['name'])
        self.assertEqual(organization.status, self.cf_organization_response['entity']['status'])

    def test_convert_response_cf_user(self):
        user = automate_cf.cf_user(self.cf_user_response)
        self.assertIsInstance(user, automate_cf.cf_user)
        self.assertEqual(user.guid, self.cf_user_response['metadata']['guid'])
        self.assertEqual(user.username, self.cf_user_response['entity']['username'])
        self.assertEqual(user.active, self.cf_user_response['entity']['active'])

    @httpretty.activate
    def test_get_quotas(self):
        url = self.autoals.url_get_quotas.substitute(apihost=self.autoals.configuration['api_host'])
        httpretty.register_uri(httpretty.GET, url,
                           body=json.dumps([self.cf_quota_response]),
                           content_type="application/json")

        quotas = self.autoals.get_quotas()
        self.assertEqual(len(quotas), 1)
        self.assertIsInstance(quotas[0], automate_cf.cf_quota)
        self.assertEqual(quotas[0].name, 'default')

    @httpretty.activate
    def test_get_organizations(self):
        url = self.autoals.url_organization.substitute(apihost=self.autoals.configuration['api_host'])
        httpretty.register_uri(httpretty.GET, url,
                           body=json.dumps([self.cf_organization_response]),
                           content_type="application/json")

        organizations = self.autoals.get_organizations()
        self.assertEqual(len(organizations), 1)
        self.assertIsInstance(organizations[0], automate_cf.cf_organization)
        self.assertEqual(organizations[0].name, 'default')

    @httpretty.activate
    def test_get_organizations_managed_by_user(self):
        url = self.autoals.url_get_organizations_managed_by_user.substitute(apihost=self.autoals.configuration['api_host'], userguid='userguid')
        httpretty.register_uri(httpretty.GET, url,
                           body=json.dumps(self.cf_organizations_managed_by_user_response),
                           content_type="application/json")

        organizations = self.autoals.get_organizations_managed_by_user('userguid')
        self.assertEqual(len(organizations), 2)
        self.assertIsInstance(organizations[0], automate_cf.cf_organization)
        self.assertEqual(organizations[1].name, 'Test Python Stuff')

    @httpretty.activate
    def test_get_user(self):
        url = self.autoals.url_get_users.substitute(apihost=self.autoals.configuration['api_host'], limit=10)
        httpretty.register_uri(httpretty.GET, url,
                           body=json.dumps([self.cf_user_response]),
                           content_type="application/json")

        users = self.autoals.get_users()
        self.assertEqual(len(users), 1)
        self.assertIsInstance(users[0], automate_cf.cf_user)
        self.assertEqual(users[0].username, 'alsautomation')


if __name__ == '__main__':
    unittest.main()
