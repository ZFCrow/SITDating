from flask import Flask, render_template, request, redirect, url_for, jsonify
from sshtunnel import SSHTunnelForwarder
from Models import db 
from DBManager import DBManager 


app = Flask(__name__)

# SSH server details
ssh_host = '35.212.133.154'
ssh_username = 'sitdate-dev'
ssh_password = 'sitokc'  # SSH password

# MySQL server details
db_host = 'localhost'
db_user = 'sitdate-sqldev'
db_password = 'sit123'
db_name = 'sit_date'
db_port = 3306

# Start SSH tunnel
server = SSHTunnelForwarder(
    (ssh_host, 22),
    ssh_username=ssh_username,
    ssh_password=ssh_password,
    remote_bind_address=(db_host, db_port)
)
server.start()

# Configure SQLAlchemy to use the tunnel
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{server.local_bind_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# pass the app to the db object 
db.init_app(app)
# db = SQLAlchemy(app)


# Dummy data for demonstration
users = [
    {"id": 1, "name": "Alice", "interests": "Reading, Hiking, Music","age": 15},
    {"id": 2, "name": "Bob", "interests": "Sports, Cooking, Traveling", "age": 20},
]

# class Users(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(50), unique=True, nullable=False)
#     password = db.Column(db.String(200), nullable=False)  # Assuming a password column exists
#     age = db.Column(db.Integer) # Assuming an age column exists 


@app.route('/')
def home():
    return render_template('home.html', users=users)

@app.route('/users')
def get_users():
    users = dbmanager.get_all_users()
    user_list = [{'id': user.id, 'username': user.username,'age':user.age, 'gender':user.gender }for user in users]
    print (user_list) 
    return jsonify(user_list)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = next((user for user in users if user["id"] == user_id), None)
    return render_template("profile.html", user=user)


@app.route("/match")
def match():
    return render_template("match.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    dbmanager = DBManager() 
    app.run(debug=True)
