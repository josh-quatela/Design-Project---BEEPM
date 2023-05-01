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


@app.route('/predictions', methods=['GET', 'POST'])
def predictions():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        predictions = predictions_data.find({
            "email": session.get('email'),
            "username": session.get('username')
        })
        html_data = '<table>'
        html_data += '<tr><th>ID</th><th>Property Name</th><th>Gross Floor Area (ft²)</th><th>Largest Property Use Type</th><th>Number of Buildings</th><th>Occupancy</th><th>Total GHG Emissions (Metric Tons CO2e)</th></tr>'
        for item in predictions:
            html_data += '<tr>'
            html_data += f'<td>{item["_id"]}</td>'
            html_data += f'<td>{item["Property Name"]}</td>'
            html_data += f'<td>{item["Self-Reported Gross Floor Area (ft²)"]}</td>'
            html_data += f'<td>{item["Largest Property Use Type"]}</td>'
            html_data += f'<td>{item["Number of Buildings"]}</td>'
            html_data += f'<td>{item["Occupancy"]}</td>'
            html_data += f'<td>{item["Total GHG Emissions (Metric Tons CO2e)"]}</td>'

            html_data += '</tr>'
        html_data += '</table>'

        return render_template("predictions.html", table=html_data)
    else:
        return render_template('login_home.html', error="Please login first.")
    

@app.route('/buildings', methods=['GET', 'POST'])
def buildings():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        buildings = ll84_data.find({
            "email": session.get('email'),
            "username": session.get('username')
        })

        html_data = '<table>'
        html_data += '<tr><th>ID</th><th>Property Name</th><th>Gross Floor Area (ft²)</th><th>Largest Property Use Type</th><th>Number of Buildings</th><th>Occupancy</th><th>Total GHG Emissions (Metric Tons CO2e)</th></tr>'
        for item in buildings:
            html_data += '<tr>'
            html_data += f'<td>{item["_id"]}</td>'
            html_data += f'<td>{item["Property Name"]}</td>'
            html_data += f'<td>{item["Self-Reported Gross Floor Area (ft²)"]}</td>'
            html_data += f'<td>{item["Largest Property Use Type"]}</td>'
            html_data += f'<td>{item["Number of Buildings"]}</td>'
            html_data += f'<td>{item["Occupancy"]}</td>'
            html_data += f'<td>{item["Total GHG Emissions (Metric Tons CO2e)"]}</td>'

            html_data += '</tr>'
        html_data += '</table>'

        return render_template("buildings.html", table=html_data)
    else:
        return render_template('login_home.html', error="Please login first.")


@app.route('/home')
def home():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        return render_template('home_logged_in.html')
    else:
        return render_template('login_home.html', error="Please login first.")


@app.route('/make_prediction', methods=['GET', 'POST'])
def make_prediction():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        return render_template('make_prediction_logged_in.html')
    else:
        return render_template('login_home.html', error="Please login first.")

@app.route('/save_prediction', methods=['GET', 'POST'])
def save_prediction():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        area_input = request.form["area_input"]
        occupancy_input = request.form["occupancy_input"]
        windows_input = request.form["windows_input"]
        height_input = request.form["height_input"]
        # TODO: run the actual prediction and get output to pass to template
        # TODO: save this prediction to the user's predictions
        prediction = "Prediction save" + area_input + ";" + occupancy_input + ";" + windows_input + ";" + height_input
        return render_template('make_prediction_logged_in.html', prediction=prediction)
    else:
        return render_template('login_home.html', error="Please login first.")

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        area_input = request.form["area_input"]
        occupancy_input = request.form["occupancy_input"]
        windows_input = request.form["windows_input"]
        height_input = request.form["height_input"]
        # TODO: run the actual prediction and get output to pass to template
        prediction = "This building sucks." +area_input+";"+occupancy_input+";"+windows_input+";"+height_input
        return render_template('make_prediction_logged_in.html', prediction=prediction)
    else:
        return render_template('login_home.html', error="Please login first.")


app.secret_key = 'very secret'
if __name__ == '__main__':
    app.run('127.0.0.1', 5000, debug=True)
