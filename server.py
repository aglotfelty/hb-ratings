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

@app.route('/users/<user_id>')
def display_user_ratings(user_id):
    """Displays user info and ratings."""

    user = User.query.get(user_id)
    return render_template("user_info.html",
                           user=user)


@app.route('/movies')
def show_movies():
    """Displays movies"""

    movies = db.session.query(Movie).order_by(Movie.title).all()
    return render_template("movies_list.html",
                            movies=movies)

@app.route('/movies/<movie_id>')
def display_movie_info(movie_id):
    """Displays movie info"""

    movie = Movie.query.get(movie_id)
    user_id = session.get("user_id")

    if user_id:
        user_rating = Rating.query.filter_by(
            movie_id=movie_id, user_id=user_id).first()

    else:
        user_rating = None

    # Get average rating of movie

    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

    prediction = None

    # Prediction code: only predict if the user hasn't rated it.

    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    # Either use the prediction or their real rating

    if prediction:
        # User hasn't scored; use our prediction if we made one
        effective_rating = prediction

    elif user_rating:
        # User has already scored for real; use that
        effective_rating = user_rating.score

    else:
        # User hasn't scored, and we couldn't get a prediction
        effective_rating = None

    # Get the eye's rating, either by predicting or using real rating

    the_eye = (User.query.filter_by(email="the_eye@gmail.com")
                         .one())
    eye_rating = Rating.query.filter_by(
        user_id=the_eye.user_id, movie_id=movie.movie_id).first()

    if eye_rating is None:
        eye_rating = the_eye.predict_rating(movie)

    else:
        eye_rating = eye_rating.score

    if eye_rating and effective_rating:
        difference = abs(eye_rating - effective_rating)*1.25

    else:
        # We couldn't get an eye rating, so we'll skip difference
        difference = None

    # Depending on how different we are from the Eye, choose a
    # message

    BERATEMENT_MESSAGES = [
        "I suppose you don't have such bad taste after all.",
        "I regret every decision that I've ever made that has " +
            "brought me to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly " +
            "failed you.",
        "That movie is great. For a clown to watch. Idiot.",
        "Words cannot express the awfulness of your taste."
    ]

    if difference is not None:
        beratement = BERATEMENT_MESSAGES[int(difference)]

    else:
        beratement = None

    return render_template(
        "movie_info.html",
        movie=movie,
        user_rating=user_rating,
        average=avg_rating,
        prediction=prediction,
        beratement=beratement,
        eye_rating=eye_rating
        )



@app.route('/rating-processed', methods=['POST'])
def process_user_rating():
    """If rating exists, update. If not, then add it to database"""

    user_rating = request.form.get("rating")
    movie_id = request.form.get("movie-id")
    user_id = session['user_id']

    if user_rating:
        try:
            movie_rating = Rating.query.filter_by(user_id=user_id, movie_id=movie_id).one()
        except Exception, e:
            rating = Rating(user_id=user_id,
                            movie_id=movie_id,
                            score=user_rating)
            db.session.add(rating)
            db.session.commit()
            flash("Your rating has been added!")
            return redirect('/movies')

        movie_rating.score = user_rating
        db.session.commit()
        flash("Your rating has been updated!")
        return redirect('/movies')
    else:
        flash("Please enter a number for your rating before clicking submit.")
        return redirect('/movies/%s' % movie_id)
        

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
        session["user_age"] = email_query.age
        session["user_zipcode"] = email_query.zipcode
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
