from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, make_response, abort, g
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, User, Category, Item
from flask_httpauth import HTTPBasicAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random, string, json, requests, httplib2

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

app = Flask(__name__)
auth = HTTPBasicAuth()

engine = create_engine('sqlite:///catalog.db', connect_args={'check_same_thread':False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# fake data
user = {'id':1, 'username':'arungp', 'password_hash':'pa55W0rd'}
users = [{'id':1, 'username':'arungp', 'password_hash':'pa55W0rd'}, {'id':2, 'username':'arungp2', 'password_hash':'pa55W0rd2'}]
category = {'id':1, 'name':'Football'}
categories = [{'id':1, 'name':'Football'}, {'id':2, 'name':'Basketball'}]
item = {'id':1, 'title':"Boots", "description":"This is the description", "category_id":1}
items = [{'id':1, 'title':"Boots", "description":"This is the description", "category_id":1}, {'id':2, 'title':"Gloves", "description":"This is the description", "category_id":1}]

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def landingPage():
    if request.method == 'GET':
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
        login_session['state'] = state
        return render_template("loginPage.html", STATE=state)
    if request.method == 'POST':
        try:
            # Check the state variable for extra security, state from ajax request should be the same as random string above
            if login_session['state'] != request.args.get('state'):
                response = make_response(json.dumps('Invalid state parameter.'), 401)
                response.headers['Content-Type'] = 'application/json'
                return response
            # If so, then retrive token sent by client
            token = request.data
            # Request an access token from the Google API
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)
            url = ('https://oauth2.googleapis.com/tokeninfo?id_token=%s' % token)
            h = httplib2.Http()
            result = json.loads(h.request(url, 'GET')[1])
            # If there was an error in the access token info, abort
            if result.get('error') is not None:
                response = make_response(json.dumps(result.get('error')), 500)
                response.headers['Content-Type'] = 'application/json'
                return response
            # Verify that the access token is used for the intended user
            user_google_id = idinfo['sub']
            if result['sub'] != user_google_id:
                response = make_response(json.dumps("Token's user ID does not match given user ID."), 401)
                response.headers['Content-Type'] = 'application/json'
                return response
            # Verify that the access token is valid for this app
            if result['aud'] != CLIENT_ID:
                response = make_response(json.dumps("Token's client ID does not match apps."), 401)
                print("Token's client ID does not match apps.")
                response.headers['Content-Type'] = 'application/json'
                return response
            # Check if the user is already logged in
            stored_access_token = login_session.get('access_token')
            stored_user_google_id = login_session.get('user_google_id')
            if stored_access_token is not None and user_google_id == stored_user_google_id:
                response = make_response(json.dumps("Current user is already connected."), 200)
                response.headers['Content-Type'] = 'application/json'
                return response
            # Store the access token in the session cookie for later use
            login_session['access_token'] = idinfo
            login_session['user_google_id'] = user_google_id
            # Get user info
            login_session['username'] = idinfo['name']
            login_session['picture'] = idinfo['picture']
            login_session['email'] = idinfo['email']
            return "Successful"
        except ValueError:
            # Invalid token
            pass


@app.route('/catalog')
def showCatalog(): # READ
    return render_template('allCategories.html', categories=categories)

# PROTECTED
@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory(): # CREATE
    return "This page will create a new category"

# PROTECTED
@app.route('/catalog/<string:category_name>/edit', methods=['GET', 'POST'])
def editCategory(category_name): # UPDATE
    return "This page will edit a category"

# PROTECTED
@app.route('/catalog/<string:category_name>/delete', methods=['GET','POST'])
def deleteCategory(category_name): # DELETE
    return "This page will delete a category"

# PROTECTED
@app.route('/catalog/<string:category_name>')
@app.route('/catalog/<string:category_name>/items')
def showItems(category_name): # READ
    # have an accordian here to expand details
    info = []
    for i in items:
        data = {}
        data['name'] = i['title']
        data['description'] = i['description']
        category_id = i['category_id']
        for j in categories:
            if j['id'] == category_id:
                data['category'] = j['name']
        info.append(data)
    return render_template('showItems.html', info=info)

@app.route('/catalog/<string:category_name>/items/<string:item_name>')
def showItemDetails(category_name, item_name): # READ
    return "This page will show the item details for a category"

# PROTECTED
@app.route('/catalog/<string:category_name>/items/new', methods=['GET', 'POST'])
def newItem(category_name): # CREATE
    return "This page will create new item for a category"

# PROTECTED
@app.route('/catalog/<string:category_name>/items/<string:item_name>/edit')
def editItem(category_name, item_name): # UPDATE
    return "This page will edit an item for a category"

# PROTECTED
@app.route('/catalog/<string:category_name>/items/<string:item_name>/delete')
def deleteItem(category_name, item_name): # DELETE
    return "This page will delete an item for a category"

# need to add JSON endpoints and login button
# also need to add login protection over certain pages

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
