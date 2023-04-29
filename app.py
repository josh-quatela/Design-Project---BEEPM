from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Sample user data
users = [
    {'username': 'user1', 'password': 'pass1'},
    {'username': 'user2', 'password': 'pass2'},
    {'username': 'user3', 'password': 'pass3'}
]


@app.route('/')
def index():
    return render_template('/Frontend/home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the username and password from the login form
        username = request.form['username_input']
        password = request.form['pass_input']
        email = request.form['email_input']

        # Check if the user is in the user list
        for user in users:
            if user['username'] == username and user['password'] == password:
                # User is authenticated, redirect to the home page
                return redirect(url_for('home'))

        # User is not authenticated, show error message
        error = 'Invalid credentials. Please try again.'
        return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/home')
def home():
    return render_template('/Frontend/home.html')


if __name__ == '__main__':
    app.run('127.0.0.1', 5000, debug=True)
