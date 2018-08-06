from flask import Flask, jsonify, abort, make_response, request
from flask_restful import Api, Resource, reqparse
from flask_httpauth import HTTPBasicAuth
import requests
import json
from copy import deepcopy

app = Flask(__name__, static_url_path="")
api = Api(app)
auth = HTTPBasicAuth()

CouchDBUser = 'admin'
CouchDBPass = 'supersecret'
CouchDBURL = 'http://dapnetdc2.db0sda.ampr.org:5984'

users = {
    "admin": "admin",
    "support": "support",
    "user": "user"
}


@auth.get_password
def get_password(username):
    if username in users:
        return users.get(username)
    return None

@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)

#class RightsAPI(Resource):
#    decorators = [auth.login_required]
#
#    def get(self):
#        if auth.username() == 'admin':
#            endpoints = [
#                '/users'
#                '
#        return jsonify(endpoints)



class UsersAPI(Resource):
    decorators = [auth.login_required]

    def get(self):
        if auth.username() == 'user':
            return make_response(jsonify({'message': 'Unauthorized access'}), 403)

        limit = request.args.get('limit')
        skip = request.args.get('skip')
        startkey = request.args.get('startkey')
        endkey = request.args.get('endkey')
        getparameters = {}
        if not (limit is None):
            getparameters['limit'] = limit
        if not (skip is None):
            getparameters['skip'] = skip
        if not (startkey is None):
            getparameters['startkey'] = startkey
        if not (endkey is None):
            getparameters['endkey'] = endkey
        getparameters['include_docs'] = 'true'
#        print (getparameters)

        r = requests.get(CouchDBURL + '/users/_all_docs',
                         auth=(CouchDBUser, CouchDBPass),
                         params=getparameters)
        print (r.status_code)
        couchdb_json = json.loads(r.content.decode('utf-8'))
        answer = {}
        answer['total_rows'] = couchdb_json['total_rows']
        answer['offset'] = couchdb_json['offset']
        answer['rows'] = []
        for row in couchdb_json['rows']:
            doc = row['doc']
            del doc['password']
            answer['rows'].append (doc)
        return answer

    def put(self):
        self.reqparseput = reqparse.RequestParser()
        self.reqparseput.add_argument('_id', type=str,
                                   location='json')
        self.reqparseput.add_argument('password', type=str,
                                   location='json')
        self.reqparseput.add_argument('email', type=str,
                                   location='json')
        self.reqparseput.add_argument('role', type=str,
                                   location='json')
        self.reqparseput.add_argument('enabled',
                                   location='json')
        self.reqparseput.add_argument('_rev',
                                   location='json')


        args = self.reqparseput.parse_args()
        if args['_id'] is None:
            return make_response(jsonify({'message': '_id missing'}), 404)
        if not( args['_rev'] is None):
# This is edit, as we have a _rev data
            if auth.username() == 'user' and args['_id'] != 'dl1abc':
                return make_response(jsonify({'message': 'Unauthorized access'}), 403)
# Test if user is existing
            r = requests.get(CouchDBURL + '/users/' + args['_id'],
                             auth=(CouchDBUser, CouchDBPass))
            print (r.status_code)
            if r.status_code != 200:
                return make_response(jsonify({'message': 'User ' + args['_id'] + \
                  ' is not existing and no _rev tag provided, so you are editing'}), 404)
            putparameters = deepcopy(args)
            putparameters['created_on'] = "2018-07-08T11:50:02.168325Z"
            putparameters['created_by'] = auth.username()
            del putparameters['_id']
            res = {k:v for k,v in putparameters.items() if v is not None}
            putparameters = res
            print (putparameters)
            r = requests.put(CouchDBURL + '/users/' + args['_id'],
                         auth=(CouchDBUser, CouchDBPass),
                         data=putparameters)
            print (r.status_code)
            print (r.content)
            if r.status_code == 200:
                return make_response(jsonify({'message': 'success'}), 200)

#        else:
# This is add new
#            if not ((auth.username() == 'admin') or (auth.username() == 'support')):
#                return make_response(jsonify({'message': 'Unauthorized access'}), 403)
# Only support and admin can add user



class UserAPI(Resource):
    decorators = [auth.login_required]

    def get(self, id):
        if auth.username() == 'user' and id != 'dl1abc':
            return make_response(jsonify({'message': 'Unauthorized access'}), 403)

        print (id)
        r = requests.get(CouchDBURL + '/users/'+id,
                         auth=(CouchDBUser, CouchDBPass))
        print (r.status_code)
        couchdb_json = json.loads(r.content.decode('utf-8'))
        del couchdb_json['password']
        return couchdb_json

class UsernamesAPI(Resource):
    decorators = [auth.login_required]

    def get(self):
        r = requests.get(CouchDBURL + '/users/_all_docs',
                         auth=(CouchDBUser, CouchDBPass))
        print (r.status_code)
        couchdb_json = json.loads(r.content.decode('utf-8'))
        answer = []
        for row in couchdb_json['rows']:
            id = row['id']
            answer.append (id)
        return answer



api.add_resource(UsersAPI, '/users', endpoint='users')
api.add_resource(UserAPI, '/users/<string:id>', endpoint='user')
api.add_resource(UsernamesAPI, '/users/_usernames', endpoint='_usernames')
#api.add_resource(RightsAPI, '/myrights', endpoint='myrights')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port = 5123)
