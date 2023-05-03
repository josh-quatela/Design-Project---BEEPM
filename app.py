# -*- coding: utf-8 -*- 
from flask import Flask, render_template, request, redirect, url_for, session
import bson

from flask import current_app, g
from werkzeug.local import LocalProxy
import pymongo
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
from bson.errors import InvalidId
import certifi

from ML import *

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

ID = None
AREA_INPUT = None
BUILDING_TYPE = None
NUM_OF_BUILDINGS = None
LETTER_GRADE = None
TOTAL_EMISSIONS = None
BUILDING_ELEC = None


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
        html_data += '<tr><th>Property ID</th><th>Gross Floor Area (Sq. Feet)</th><th>Property Use Type</th><th>Number of Buildings</th><th>Letter Grade</th><th>Total GHG Emissions (Metric Tons CO2e)</th><th>Total Electricity Use</th><th>Save Building</th></tr>'
        for item in predictions:
            #html_data += '<tr>'

            #<form method="post" action="{{ url_for('save_building') }}">

             html_data += f'''<tr>
                            <td id="id" name="id">{str(item["_id"])}</td>
                            <td id="area_input" name="area_input">{str(item["area_input"])}</td>
                            <td id="building_type" name="building_type">{str(item["building_type"])}</td>
                            <td id="number_of_buildings" name="number_of_buildings">{str(item["number_of_buildings"])}</td>
                            <td id="letter_grade" name="letter_grade">{str(item["letter_grade"])}</td>
                            <td id="total_emissions" name="total_emissions">{str(item["total_emissions"])}</td>
                            <td id="building_electricity" name="building_electricity">{str(item["building_electricity"])}</td>
                            <td>
                                <form method="post" action="/save_building">
                                    <input type="hidden" name="id" value="{str(item["_id"])}">
                                    <input type="hidden" name="area_input" value="{str(item["area_input"])}">
                                    <input type="hidden" name="building_type" value="{str(item["building_type"])}">
                                    <input type="hidden" name="number_of_buildings" value="{str(item["number_of_buildings"])}">
                                    <input type="hidden" name="letter_grade" value="{str(item["letter_grade"])}">
                                    <input type="hidden" name="total_emissions" value="{str(item["total_emissions"])}">
                                    <input type="hidden" name="building_electricity" value="{str(item["building_electricity"])}">
                                    <button type="submit">Save Building</button>
                                </form>
                            </td>
                        </tr>'''


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
        html_data += '<tr><th>Property Name</th><th>Gross Floor Area (Sq. Feet)</th><th>Largest Property Use Type</th><th>Number of Buildings</th><th>Total GHG Emissions (Metric Tons CO2e)</th></tr>'
        for item in buildings:
            html_data += '<tr>'
            html_data += '<td>' + item["Property Name"] + '</td>'
            html_data += '<td>' + item["Self-Reported Gross Floor Area (ft²)"] + '</td>'
            html_data += '<td>' + item["Largest Property Use Type"] + '</td>'
            html_data += '<td>' + item["Number of Buildings"] + '</td>'
            html_data += '<td>' + item["Total GHG Emissions (Metric Tons CO2e)"] + '</td>'
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
        number_of_buildings = request.form["windows_input"] 
        building_type = request.form["height_input"]
        #run the actual prediction and get output to pass to template
        pred = get_prediction(building_type, int(occupancy_input), int(number_of_buildings), int(area_input))
        letter_grade = pred[0]
        #save this prediction to the user's predictions
        total_emissions = pred[1][0]
        building_electricity = pred[1][1]
        predictions_data.insert_one({"email": session.get('email'), "username": session.get('username'), "building_type": building_type, "occupancy_input": occupancy_input, "number_of_buildings": number_of_buildings, "area_input": area_input, "letter_grade": letter_grade, "total_emissions": total_emissions, "building_electricity": building_electricity})
        prediction = "Prediction saved!" + area_input + " Sq. Feet; " + occupancy_input + " Occupancy; " + number_of_buildings + building_type + " Building"
        return render_template('make_prediction_logged_in.html', prediction=prediction)
    else:
        return render_template('login_home.html', error="Please login first.")

@app.route('/save', methods=['GET', 'POST'])
def save():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        ll84_data.insert_one({"Property Id": session.get('build_id'),
                              "Property Name": request.form["building_name"],
                              "Self-Reported Gross Floor Area (ft²)": session.get("area_input"),
                              "Number of Buildings": session.get("number_of_buildings"),
                              "Largest Property Use Type": session.get("building_type"),
                              "Total GHG Emissions (Metric Tons CO2e)": session.get("total_emissions"),
                              "Electricity Use": session.get("building_electricity"),
                              "email": session.get('email'),
                              "username": session.get('username')
                              })

        return redirect(url_for("buildings"))
    else:
        return render_template('login_home.html', error="Please login first.")

@app.route('/save_building', methods=['GET', 'POST'])
def save_building():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        build_id = request.form["id"]
        area_input = request.form["area_input"]
        building_type = request.form["building_type"]
        number_of_buildings = request.form["number_of_buildings"]
        letter_grade = request.form["letter_grade"]
        total_emissions = request.form["total_emissions"]
        building_electricity = request.form["building_electricity"]

        session["build_id"] = request.form["id"]
        session["area_input"] = request.form["area_input"]
        session["building_type"] = request.form["building_type"]
        session["number_of_buildings"] = request.form["number_of_buildings"]
        session["letter_grade"] = request.form["letter_grade"]
        session["total_emissions"] = request.form["total_emissions"]
        session["building_electricity"] = request.form["building_electricity"]

        return render_template('save_building.html',
                               build_id=build_id,
                               area_input=area_input,
                               building_type=building_type,
                               number_of_buildings=number_of_buildings,
                               letter_grade=letter_grade,
                               total_emissions=total_emissions,
                               building_electricity=building_electricity)
    else:
        return render_template('login_home.html', error="Please login first.")

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    check_logged = login_data.find_one( {"email" : session.get('email'), "username" : session.get('username')})
    if check_logged:
        area_input = request.form["area_input"]
        occupancy_input = request.form["occupancy_input"]
        number_of_buildings = request.form["windows_input"] 
        building_type = request.form["height_input"] 
        #run the actual prediction and get output to pass to template
        pred = get_prediction(building_type, int(occupancy_input), int(number_of_buildings), int(area_input))
        #print(pred)
        letter_grade = pred[0]
        prediction = "This building has a grade of " + letter_grade
        str_output = get_analysis(pred)
        prediction = str_output
        
        return render_template('make_prediction_logged_in.html', prediction=prediction)
    else:
        return render_template('login_home.html', error="Please login first.")


app.secret_key = 'very secret'
if __name__ == '__main__':
    app.run('127.0.0.1', 5000, debug=True)
