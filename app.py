from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash,
    session,
    
)
from sshtunnel import SSHTunnelForwarder
from Models import db, SwipeRight, Matches
from DBManager import DBManager


app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"


# SSH server details
ssh_host = "35.212.133.154"
ssh_username = "sitdate-dev"
ssh_password = "sitokc"  # SSH password

# MySQL server details
db_host = "localhost"
db_user = "sitdate-sqldev"
db_password = "sit123"
db_name = "sit_date"
db_port = 3306

# Start SSH tunnel
server = SSHTunnelForwarder(
    (ssh_host, 22),
    ssh_username=ssh_username,
    ssh_password=ssh_password,
    remote_bind_address=(db_host, db_port),
)
server.start()


# Configure SQLAlchemy to use the tunnel
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{server.local_bind_port}/{db_name}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# pass the app to the db object
db.init_app(app)
dbmanager = DBManager()

# with app.app_context():
#     db.create_all() # Create tables


@app.route("/")
def home():
    username = None
    if 'user_id' in session:
        user = dbmanager.get_user_by_id(session['user_id'])
        if user:
            username = user.username
    return render_template('home.html', users=dbmanager.get_all_users(), username=username)


@app.route("/users")
def get_users():
    users = dbmanager.get_all_users()
    user_list = [
        {
            "id": user.id,
            "username": user.username,
            "age": user.age,
            "gender": user.gender,
        }
        for user in users
    ]
    print(user_list)
    return jsonify(user_list)


@app.route("/profile/<int:user_id>")
def profile(user_id):
    user = next((user for user in users if user["id"] == user_id), None)
    return render_template("profile.html", user=user)


@app.route("/match")
def match():
    #retrieve the user id from the session 
    user_id = session['user_id'] 
    matches = dbmanager.get_matches(user_id) 
    for match in matches:
        print(match.username)
        print (match.age) 
    return render_template("match.html", matches = matches)

@app.route("/swipe-right", methods=["POST"])
def swipe_right():
    data = request.get_json()
    userID = session['user_id']
    swipeeID = data['user_id'] 
    print (userID, swipeeID)

    response = dbmanager.add_swipe_right(userID, swipeeID)

    #check if its a match or a swipe right 
    if isinstance(response, Matches):
        print ("Match")
        return jsonify({"status": "match"}), 200
    elif isinstance(response, SwipeRight):
        print ("Swipe Right") 
        return jsonify({"status": "swipe right"}), 200
        
    

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        print("inside post")
        # Extract data from form
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        gender = request.form.get("gender")
        age = request.form.get("age")
        course = request.form.get("course")
        interests = request.form.get("interests")
        password = request.form.get("password")
        confirmpassword = request.form.get("confirmpassword")
        print(name, username)

        # Check if passwords match
        if password != confirmpassword:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))

        # Save user to database
        dbmanager.add_user(
            username, password, name, age, gender, interests, course, email
        )

        flash("Registration successful!", "success")
        return redirect(url_for("preference"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        print(email, password)
        user = dbmanager.get_user_by_email(email)
        if user and user.password == password:
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        flash("Invalid email or password", "danger")

    return render_template("login.html")


@app.route("/preference")
def preference():
    return render_template("preference.html")



@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out", "info")
    return redirect(url_for("home"))


@app.route("/delete/<int:user_id>")
def delete_user(user_id):
    dbmanager.delete_user(user_id)
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
