from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dummy data for demonstration
users = [
    {"id": 1, "name": "Alice", "interests": "Reading, Hiking, Music"},
    {"id": 2, "name": "Bob", "interests": "Sports, Cooking, Traveling"},
]

@app.route('/')
def home():
    return render_template('home.html', users=users)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = next((user for user in users if user["id"] == user_id), None)
    return render_template('profile.html', user=user)

@app.route('/match')
def match():
    return render_template('match.html')

if __name__ == '__main__':
    app.run(debug=True)
