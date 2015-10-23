#-------------------------------------------------------------------------------
# Name:        onboarding
# Purpose:     facilitate onboarding of new tenants/projects and organizations
#              in Helion OpenStack and Helion Stackato
#
# Author:      Daniel Watrous
#
# Created:     04/14/2015
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
import bottle
import json
import ldap
import jwt
import time
import automate_cf
import automate_openstack

jwtsecret = '0d32abe5e55bfe6019398a3ef9580709d6b40afd'

class MyJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__

appv1 = bottle.Bottle(autojson=False)
appv1.install(bottle.JSONPlugin(json_dumps=lambda s: json.dumps(s, cls=MyJsonEncoder, encoding="utf8"))) # NOTE: http://directory.hp.com/dirdata/UTF8.html

api_version = {'version': '1.0 r1'}

@appv1.error(400)
@appv1.error(401)
@appv1.error(404)
@appv1.error(500)
def error_json_generic(error):
    try:
        error_details = json.loads(error.body)
    except:
        error_details = error.body
    enable_cors()
    bottle.response.content_type = 'application/json'
    return json.dumps({"error_message": error_details})

autocf = automate_cf.automate_cf()
#autohos = automate_openstack.automate_openstack_v2()

class AuthorizationError(Exception):
    """ A base class for exceptions used by bottle. """
    pass

#@bottle.hook('after_request')  # this doesn't work, so I added the add_hook call below
def enable_cors():
    origin = bottle.request.headers.get('Origin', None)
    if origin:
        bottle.response.headers['Access-Control-Allow-Origin'] = origin
        bottle.response.headers['Access-Control-Allow-Methods'] = 'GET, PUT, POST, DELETE'
        bottle.response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'

appv1.add_hook('after_request', enable_cors)

@appv1.route('/<:re:.*>', method='OPTIONS')
def options():
    return 'OPTIONS'

def jwt_token_from_header():
    auth = bottle.request.headers.get('Authorization', None)
    if not auth:
        raise AuthorizationError({'code': 'authorization_header_missing', 'description': 'Authorization header is expected'})

    parts = auth.split()

    if parts[0].lower() != 'bearer':
        raise AuthorizationError({'code': 'invalid_header', 'description': 'Authorization header must start with Bearer'})
    elif len(parts) == 1:
        raise AuthorizationError({'code': 'invalid_header', 'description': 'Token not found'})
    elif len(parts) > 2:
        raise AuthorizationError({'code': 'invalid_header', 'description': 'Authorization header must be Bearer + \s + token'})

    return parts[1]

def requires_auth(f):
    """Provides JWT based authentication for any decorated function assuming credentials available in an "Authorization" header"""
    def decorated(*args, **kwargs):
        try:
            token = jwt_token_from_header()
        except AuthorizationError, reason:
            bottle.abort(400, reason.message)

        try:
            jwt.decode(token, jwtsecret)    # throw away value
        except jwt.ExpiredSignature:
            bottle.abort(401, {'code': 'token_expired', 'description': 'token is expired'})
        except jwt.DecodeError, message:
            bottle.abort(401, {'code': 'token_invalid', 'description': message.message})

        return f(*args, **kwargs)

    return decorated

def get_jwt_credentials():
    # get and decode the current token
    token = jwt_token_from_header()
    credentials = jwt.decode(token, jwtsecret)
    return credentials

@appv1.route('/')
def index():
    output = bottle.template('<b>Nothing to see here</b>. This is a RESTful API designed for computers.')
    return output

@appv1.get('/v1/version')
def get_api_version():
    return api_version

@appv1.get('/v1/als/user')
@requires_auth
def get_user_details():
    desired_user = None
    # if a querystring parameter username is present, search for that user
    if bottle.request.query.username:
        desired_user = bottle.request.query.username
    # otherwise use the logged in user
    else:
        desired_user = get_jwt_credentials()['user']

    try:
        return {'user': autocf.find_user_by_username(desired_user)}
    except:
        bottle.abort(404, 'No user with username %s was found.' % desired_user)

@appv1.put('/v1/als/user')
@requires_auth
def create_user():
    try:
        return {'user': autocf.create_user(bottle.request.json['username'])}
    except Exception as error:
        bottle.abort(error.message['status'], error.message['message'])

@appv1.get('/v1/als/user/organizations')
@requires_auth
def get_orgs_for_user():
    current_user = autocf.find_user_by_username(get_jwt_credentials()['user'])
    return {'organizations': autocf.get_organizations_for_user(current_user.guid)}

@appv1.get('/v1/als/user/organizations/managed')
@requires_auth
def get_orgs_managed_by_user():
    current_user = autocf.find_user_by_username(get_jwt_credentials()['user'])
    return {'organizations': autocf.get_organizations_managed_by_user(current_user.guid)}


@appv1.get('/v1/als/organizations')
@requires_auth
def get_organizations():
    # if a querystring parameter organizationname is present, search for that organization
    if bottle.request.query.orgname:
        desired_organization = bottle.request.query.orgname
        return {'organizations': autocf.find_organizations_by_name(desired_organization)}
    # otherwise return all organizations
    else:
        return {'organizations': autocf.get_organizations()}

@appv1.get('/v1/als/organizations/<orgid>')
@requires_auth
def get_organization(orgid):
    for org in autocf.get_organizations():
        if org.guid == orgid:
            return org.__dict__
    bottle.abort(404, 'No organization with name %s was found.' % orgid)

@appv1.put('/v1/als/organizations')
@requires_auth
def create_organization():
    orgdetails = bottle.request.json
    return autocf.create_organization(orgdetails['organization']['name']).__dict__

@appv1.get('/v1/als/organizations/<orgid>/users')
@requires_auth
def get_users_for_organization(orgid):
    return {'users': autocf.get_users_for_organization(orgid)}

@appv1.put('/v1/als/organizations/<orgid>/users/<userid>')
@requires_auth
def add_user_to_organization(orgid, userid):
    return {'organization': autocf.add_user_to_organization(userid, orgid)}

@appv1.delete('/v1/als/organizations/<orgid>/users/<userid>')
@requires_auth
def remove_user_from_organization(orgid, userid):
    return {'organization': autocf.remove_user_from_organization(userid, orgid)}

@appv1.get('/v1/als/organizations/<orgid>/managers')
@requires_auth
def get_managers_for_organization(orgid):
    return {'users': autocf.get_organization_managers_by_guid(orgid)}

@appv1.put('/v1/als/organizations/<orgid>/managers/<userid>')
@requires_auth
def add_user_as_manager_for_organization(orgid, userid):
    return {'organization': autocf.make_user_manager(userid, orgid)}

@appv1.delete('/v1/als/organizations/<orgid>/managers/<userid>')
@requires_auth
def remove_user_as_manager_from_organization(orgid, userid):
    return {'organization': autocf.remove_user_manager(userid, orgid)}

if __name__ == '__main__':
    port = int(os.getenv('PORT', '8000'))
    bottle.run(appv1, host='0.0.0.0', port=port, reloader=False, debug=True)
else:
    application = appv1