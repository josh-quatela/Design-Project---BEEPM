from flask import Flask, render_template, request, redirect, url_for, session
import bson

from flask import current_app, g
from werkzeug.local import LocalProxy
import pymongo
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId
import certifi


app = Flask(__name__)

app.config['MONGODB_SETTINGS'] = {
    'db': 'beepm1',
    'host': 'mongodb+srv://beepmrw:Beepm@beepm1.21uirez.mongodb.net/'
}

client = pymongo.MongoClient(
    "mongodb+srv://beepmrw:Beepm@beepm1.21uirez.mongodb.net/test?retryWrites=true&w=majority&ssl=true", 
    tlsCAFile=certifi.where())
client.admin.command('ping')
print("Pinged your deployment. You successfully connected to MongoDB!")
    
connected_db = client.beepm_data
login_data = connected_db["logins"]
ll84_data = connected_db["ll84"]
predictions_data = connected_db["predictions"]



@app.route('/')
def index():
    return render_template('home.html')


@app.route('/login_home', methods=['GET', 'POST'])
def login_home():
    if request.method == 'POST':
        return redirect(url_for("login"))
    else:
        return render_template('login_home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the username and password from the login form
        username = request.form['username_input']
        password = request.form['pass_input']
        email = request.form['email_input']

        print("USER: ", username)
        print("PASS: ", password)
        print("EMAIL: ", email)

        #change based on html/css, just not familiar enough with how it's laid out to do this myself
        if request.form.get('login'): #trying existing login
            print("checking for login")
            # Check if the user is in the user list
            returned = login_data.find_one( {
                "email": email,
                "username": username,
                "password": password
            } )
            if returned:
                session['email'] = email
                session['username'] = username
                return redirect(url_for('home'))
            # User is not authenticated, show error message
            error = 'Invalid credentials. Please try again.'
            print(error)
            return render_template('login_home.html', error=error)
        else: #creating a new user
            returned = login_data.find_one( {
            "email": email,
            "username": username
            } )
            if returned:
                error = 'Account already exists.'
                print(error)
                return render_template('login_home.html', error=error)
        # User is not authenticated, show error message
            print(login_data.insert_one({"email": email, "username": username, "password": password}))
            session['email'] = email
            session['username'] = username
            return redirect(url_for('home'))
    
    return render_template('home_logged_in.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return render_template('home.html')


@app.route('/my_predictions', methods=['GET', 'POST'])
def my_predictions():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        predictions = predictions_data.find({
            "email": session.get('email'),
            "username": session.get('username')
        })
        #should be able to use predictions as the data to put into the html table, just not sure where that html page is
    else:
        return render_template('login_home.html', error="Please login first.")
    

@app.route('/my_buildings', methods=['GET', 'POST'])
def my_buildings():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        buildings = ll84_data.find({
            "email": session.get('email'),
            "username": session.get('username')
        })
        #should be able to use buildings as the data to put into the html table, just not sure where that html page is
    else:
        return render_template('login_home.html', error="Please login first.")


@app.route('/home')
def home():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        return render_template('home_logged_in.html')
    else:
        return render_template('login_home.html', error="Please login first.")


app.secret_key = 'very secret'
if __name__ == '__main__':
    app.run('127.0.0.1', 5000, debug=True)
