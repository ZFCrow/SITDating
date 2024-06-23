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
from werkzeug.utils import secure_filename
import cv2
import pytesseract
import re
import os
import constants

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"


# SSH server details
ssh_host = constants.ssh_host 
ssh_username = constants.ssh_username
ssh_password = constants.ssh_password

# MySQL server details
db_host = constants.db_host
db_user = constants.db_user
db_password = constants.db_password
db_name = constants.db_name
db_port = constants.db_port

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

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# pass the app to the db object
db.init_app(app)
dbmanager = DBManager()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route("/")
def home():
    username = None
    filteredUsers = [] 
    if "user_id" in session:
        user = dbmanager.get_user_by_id(session["user_id"])
        if user:
            username = user.username
        #go to user preference table, get the user preferences and filter the users based on the preferences 
        #get the user preferences 
        preferences = dbmanager.get_user_preferences(session["user_id"])
        if not preferences:
            flash("Please set your preferences", "danger")
            return redirect(url_for("preference"))
        preFerredGender = preferences.preferred_gender
        preferredAgeMin = preferences.preferred_age_min
        preferredAgeMax = preferences.preferred_age_max
        preferredInterests = preferences.interests.split(",") if preferences.interests else []
        print (f"PreferredGender: {preFerredGender}, PreferredAgeMin: {preferredAgeMin}, PreferredAgeMax: {preferredAgeMax}, PreferredInterests: {preferredInterests}")
        users = dbmanager.get_all_users()
        
        #filter the users based on the preferences
        filteredUsers = [
            user for user in users
            if (user.gender == preFerredGender or preFerredGender == "Any") and
            (user.age >= preferredAgeMin and user.age <= preferredAgeMax)
        ]
        print(filteredUsers)

    return render_template("home.html", users=filteredUsers, username=username)


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
    user = dbmanager.get_user_by_id(session["user_id"])
    # user = next((user for user in users if user["id"] == user_id), None)
    return render_template("profile.html", user=user)


@app.route("/match")
def match():
    # retrieve the user id from the session
    # check if the session has a user id
    if "user_id" not in session:
        flash("Please login to view your matches", "danger")
        return redirect(url_for("login"))
    user_id = session["user_id"]
    matches = dbmanager.get_matches(user_id)
    for match in matches:
        print(match.username)
        print(match.age)
    return render_template("match.html", matches=matches)


@app.route("/swipe-right", methods=["POST"])
def swipe_right():
    data = request.get_json()
    userID = session["user_id"]
    swipeeID = data["user_id"]
    print(userID, swipeeID)

    response = dbmanager.add_swipe_right(userID, swipeeID)

    # check if its a match or a swipe right
    if isinstance(response, Matches):
        print("Match")
        return jsonify({"status": "match"}), 200
    elif isinstance(response, SwipeRight):
        print("Swipe Right")
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
        user_card_image = request.files['user_card_image']
        print(name, username)

        # Check if passwords match
        if password != confirmpassword:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))

        if user_card_image and allowed_file(user_card_image.filename):
            user_card_image_filename = secure_filename(user_card_image.filename)
            user_card_image_path = os.path.join(app.config['UPLOAD_FOLDER'], user_card_image_filename)
            print (f"{user_card_image_path}") 
            user_card_image.save(user_card_image_path)

        if not detect_school_card(user_card_image_path):
            flash("Invalid user card", "danger")
            return redirect(url_for("register"))
        
        # Save user to database
        dbmanager.add_user(
            username, password, name, age, gender, interests, course, email
        )

        flash("Registration successful!", "success")
        # retrive userID from the database
        user = dbmanager.get_user_by_email(email)
        print(user.id)
        session["user_id"] = user.id
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


@app.route("/preference", methods=["GET", "POST"])
def preference():
    if "user_id" not in session:
        flash("Please login to set your preferences", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        print("receive preference form")
        # Extract data from form
        gender = request.form.get("gender")
        min_age = request.form.get("min_age")
        max_age = request.form.get("max_age")
        interests = request.form.get("interests") 
        user_id = session['user_id']
        print (f"User ID: {user_id}, min_age: {min_age}, max_age: {max_age}, interests: {interests}, user_id: {user_id}")
        # if max age is less than min age, flash an error message 
        if int(max_age) < int(min_age): 
            flash("Max age cannot be less than min age", "danger")
            return redirect(url_for("preference")) 
        dbmanager.add_preference(user_id=user_id, preferred_age_min=min_age, preferred_age_max=max_age, preferred_gender=gender, interests=interests)
        flash("Preferences saved!", "success") 
        return redirect(url_for("home")) 
        
    return render_template("preference.html")

# Normalize extracted text (remove non-alphanumeric characters and convert to lowercase)
def normalize_text(text):
    text = re.sub(r'\W+', '', text)  # Remove non-alphanumeric characters
    text = text.lower()  # Convert to lowercase
    return text

# Function to validate if the extracted text indicates a valid school card
def validate_user_card(text):
    # Normalize text (convert to lowercase and remove extra spaces)
    normalized_text = text.lower().strip().replace("\n", " ")
    print (f"Normalized Text: {normalized_text}")   
    # Define keywords and patterns
    keywords = ["singapore institute of technology", "sit", "student"]

    # Check for keywords in the normalized text
    for keyword in keywords:
        if keyword in normalized_text:
            print (f"{keyword} Keyword found") 
            return True
        print ("Keyword not found") 

    # Check for a 7-digit number using regular expression
    seven_digit_pattern = re.compile(r'\b\d{7}\b')
    if seven_digit_pattern.search(normalized_text):
        print("7-digit number found")
        return True
    else:
        print("No 7-digit number found")


    return False

# Main function to process an image and validate if it's a school card
def detect_school_card(image_path):
    # Preprocess the image
    preprocessed_image = preprocess_image(image_path)

    # Perform OCR on preprocessed image
    extracted_text = perform_ocr(preprocessed_image)

    # Validate the extracted text
    if validate_user_card(extracted_text):
        print("Valid school card detected.")
        return True 
    else:
        print("Not a valid school card.")
        return False
    # Optionally, print the extracted text for debugging purposes
    print("Extracted Text:")
    print(extracted_text)





# Function to preprocess the image
def preprocess_image(image_path):
    # Load image using OpenCV
    image = cv2.imread(image_path)

    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    return blur

# Function to perform OCR on preprocessed image
def perform_ocr(image):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # Use Tesseract OCR to extract text
    text = pytesseract.image_to_string(image)

    return text



def detect_sit_logo(img):
    # Load the SIT logo template
    logo_template = cv2.imread('static/images/schoolLogo.jpg', 0)
    
    # Check if the template is larger than the source image
    img_height, img_width = img.shape[:2]
    template_height, template_width = logo_template.shape[:2]

    # Resize the template if necessary
    if template_height > img_height or template_width > img_width:
        print ("Resizing template") 
        scale_ratio = min(img_height / template_height, img_width / template_width)
        new_dimensions = (int(template_width * scale_ratio), int(template_height * scale_ratio))
        logo_template = cv2.resize(logo_template, new_dimensions)

    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray_img, logo_template, cv2.TM_CCOEFF_NORMED)

    threshold = 0.8
    loc = cv2.minMaxLoc(result)
    if loc[1] >= threshold:
        print ("SIT logo detected") 
        return True
    print (loc[1]) 
    print ("SIT logo not detected") 
    return False

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
