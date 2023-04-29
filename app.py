from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Sample user data
users = [
    {'username': 'user1', 'email': 'email1', 'password': 'pass1'},
    {'username': 'user2', 'email': 'email2', 'password': 'pass2'},
    {'username': 'user3', 'email': 'email3', 'password': 'pass3'}
]


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

        # Check if the user is in the user list
        for user in users:
            if user['username'] == username and user['password'] == password and user['email'] == email:
                # User is authenticated, redirect to the home page
                return redirect(url_for('home'))

        # User is not authenticated, show error message
        error = 'Invalid credentials. Please try again.'
        print(error)
        return render_template('login_home.html', error=error)

    return render_template('home_logged_in.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    return render_template('home.html')


@app.route('/home')
def home():
    return render_template('home_logged_in.html')


if __name__ == '__main__':
    app.run('127.0.0.1', 5000, debug=True)
