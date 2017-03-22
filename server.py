"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, jsonify, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Rating, Movie


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/users')
def show_users():
    """Displays users as email and id"""

    users = db.session.query(User).all()
    return render_template("user_list.html",
                            users=users)

@app.route('/registration')
def show_registration_form():
    """Displays registration form"""

    return render_template("registration.html")

@app.route('/registration-complete', methods=['POST'])
def check_user():
    """Checks if user exists, if not, creates new user."""

    user_email = request.form.get("email")
    user_password = request.form.get("password")
    user_age = request.form.get("age")
    user_zipcode = request.form.get("zipcode")
    email_query = User.query.filter_by(email=user_email).all()
    if email_query:
        print "This user already exists"
    else:
        user = User(email=user_email, password=user_password, age=user_age, zipcode=user_zipcode)
        db.session.add(user)
        db.session.commit()
    return redirect("/")

@app.route('/login')
def show_login():
    """Displays login form"""

    return render_template("login.html")

@app.route('/login-completed')
def process_login_info():
    """Checks if user email and password exist on same account"""

    user_email = request.args.get("email")
    user_password = request.args.get("password")
    
    try:
        email_query = User.query.filter_by(email=user_email).one()
    except Exception, e:
        email_query = False

    if email_query and email_query.password == user_password:
        session["user_id"] = email_query.user_id
        session["user_email"] = email_query.email
        session["user_password"] = email_query.password
        session["user_age"] = email_query.age
        session["user_zipcode"] = email_query.zipcode
        session["user_ratings"] = Rating.query.filter_by(user_id=email_query.user_id).all()
        print session
        flash("You have successfully logged in!")
        return redirect("/")
    else:
        flash("Email or Password is incorrect. Please try again!")
        return redirect("/login")

@app.route('/logout-completed')
def process_logout_info():
    """Checks if user email and password exist on same account"""

    session = {}
    print session
    flash("You have successfully logged out! We hope you come back soon")
    return redirect("/")

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)


    
    app.run(port=5000, host='0.0.0.0')
