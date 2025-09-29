from flask import Flask, render_template, request, redirect, make_response, url_for
import mysql.connector
import bcrypt
import jwt
import datetime
import re
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = "6LeeANQrAAAAANCERRtSdlwa6ODRSy-JuJJT5Ku_"

# MySQL 
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="K@rthik2147",
    database="vault"
)
cursor = conn.cursor(dictionary=True)


# JWT Utils
def generate_jwt(user_id, username, role):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

def decode_jwt(token):
    try:
        return jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
    except:
        return None

# reCAPTCHA Verification
def verify_captcha(response_token):
    secret = "6LeeANQrAAAAANCERRtSdlwa6ODRSy-JuJJT5Ku_"
    verify_url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {"secret": secret, "response": response_token}
    r = requests.post(verify_url, data=payload)
    result = r.json()
    return result.get("success", False)

# Login Required Decorator
def login_required(role=None):
    def wrapper(func):
        def decorated_function(*args, **kwargs):
            token = request.cookies.get("jwt_token")
            if not token:
                return redirect("/")
            user_data = decode_jwt(token)
            if not user_data:
                return redirect("/")
            if role and user_data["role"] != role:
                return redirect("/")
            return func(user_data, *args, **kwargs)
        decorated_function.__name__ = func.__name__
        return decorated_function
    return wrapper

# Home Page
@app.route("/")
def home():
    return render_template("index.html")
# About Page
@app.route("/about")
def about():
    return render_template("about.html")

# Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        role = request.form["role"].strip().lower()

        if role not in ["admin", "user"]:
            return "Invalid role selected", 400
        if not re.match(r"^[A-Za-z0-9_]{3,20}$", username):
            return "Invalid username", 400
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            return "Invalid email", 400
        if len(password) < 8:
            return "Password must be at least 8 characters", 400

        cursor.execute("SELECT id FROM user WHERE username=%s OR email_id=%s", (username, email))
        if cursor.fetchone():
            return "Username or Email already exists", 400

        cursor.execute("SELECT id FROM user_role WHERE name=%s", (role,))
        row = cursor.fetchone()
        if not row:
            return "Role not found", 400
        role_id = row["id"]

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO user (username, email_id, password, role_id, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (username, email, hashed_password, role_id)
        )
        conn.commit()
        return redirect("/")
    return render_template("register.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"].strip()
    password = request.form["password"]
    role = request.form["role"].strip().lower()
    captcha_response = request.form.get("g-recaptcha-response")

    if not captcha_response or not verify_captcha(captcha_response):
        return "CAPTCHA failed", 400

    cursor.execute(
        "SELECT u.id, u.password, u.username, r.name FROM user u "
        "JOIN user_role r ON u.role_id=r.id "
        "WHERE u.username=%s AND r.name=%s",
        (username, role)
    )
    user = cursor.fetchone()
    if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return "Invalid credentials", 401

    cursor.execute(
        "INSERT INTO login_activity (user_id, username_snapshot, login_time) VALUES (%s, %s, NOW())",
        (user["id"], user["username"])
    )
    conn.commit()

    token = generate_jwt(user["id"], user["username"], user["name"])
    resp = make_response(redirect("/admin" if user["name"] == "admin" else "/user_dashboard"))
    resp.set_cookie("jwt_token", token, httponly=True, secure=False)
    return resp


# Admin Dashboard
@app.route("/admin")
@login_required(role="admin")
def admin_dashboard(user_data):
    cursor.execute(
        "SELECT u.id, u.username, u.email_id, r.name AS role, u.created_at "
        "FROM user u JOIN user_role r ON u.role_id=r.id"
    )
    users = cursor.fetchall()
    return render_template("admin_dashboard.html", users=users, current_user_id=user_data["user_id"])

# Login Activity
@app.route("/login_activity/<int:user_id>")
@login_required(role="admin")
def login_activity(user_data, user_id):
    cursor.execute("SELECT username, created_at FROM user WHERE id=%s", (user_id,))
    user_info = cursor.fetchone()

    cursor.execute(
        "SELECT username_snapshot, login_time, logout_time "
        "FROM login_activity WHERE user_id=%s ORDER BY login_time DESC",
        (user_id,)
    )
    activity = cursor.fetchall()

    return render_template("login_activity.html", user_info=user_info, activity=activity)



# Change Role
@app.route("/change_role/<int:user_id>", methods=["POST"])
@login_required(role="admin")
def change_role(user_data, user_id):
    if user_data["user_id"] == user_id:
        return "Cannot change your own role!", 400

    new_role = request.form.get("role")
    cursor.execute("SELECT id FROM user_role WHERE name=%s", (new_role,))
    role_row = cursor.fetchone()
    if not role_row:
        return "Role not found", 400
    role_id = role_row["id"]
    cursor.execute("UPDATE user SET role_id=%s WHERE id=%s", (role_id, user_id))
    conn.commit()
    return redirect("/admin")

# Delete User
@app.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required(role="admin")
def delete_user(user_data, user_id):
    if user_data["user_id"] == user_id:
        return "Cannot delete yourself!", 400
    cursor.execute("DELETE FROM user WHERE id=%s", (user_id,))
    conn.commit()
    return redirect("/admin")

# User Dashboard
@app.route("/user_dashboard")
@login_required()
def user_dashboard(user_data):
    cursor.execute("SELECT username, email_id, created_at FROM user WHERE id=%s", (user_data["user_id"],))
    user = cursor.fetchone()
    return render_template("user_dashboard.html", user=user)

@app.route("/logout")
def logout():
    token = request.cookies.get("jwt_token")
    user_data = decode_jwt(token) if token else None

    if user_data:
        cursor.execute(
            "UPDATE login_activity SET logout_time = NOW() "
            "WHERE user_id = %s AND logout_time IS NULL "
            "ORDER BY login_time DESC LIMIT 1",
            (user_data["user_id"],)
        )
        conn.commit()

    resp = make_response(redirect("/"))
    resp.delete_cookie("jwt_token")
    return resp

if __name__ == "__main__":
    app.run(debug=True)
