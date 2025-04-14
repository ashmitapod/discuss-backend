import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS  # Import is already here
from marshmallow import ValidationError
import cloudinary
from flask_login import LoginManager
from threaddit.config import (
    DATABASE_URI,
    SECRET_KEY,
    CLOUDINARY_API_SECRET,
    CLOUDINARY_API_KEY,
    CLOUDINARY_NAME,
)

# Use the backend/static folder for serving frontend static
static_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../static")

app = Flask(
    __name__,
    static_folder=static_folder_path,
    static_url_path="/",
)

# Add this line to initialize CORS - this is what was missing
CORS(app, resources={r"/*": {"origins": "https://discuss-frontend.vercel.app", "supports_credentials": True}})

# Cloudinary config
cloudinary.config(
    cloud_name=CLOUDINARY_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)

# Flask app config
app.config["CLOUDINARY_NAME"] = CLOUDINARY_NAME
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SECRET_KEY"] = SECRET_KEY

# Init extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
ma = Marshmallow(app)

@login_manager.unauthorized_handler
def callback():
    return jsonify({"message": "Unauthorized"}), 401

# Serve frontend routes from static/index.html
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    return app.send_static_file("index.html")

@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify({"errors": err.messages}), 400

@app.errorhandler(404)
def not_found(e):
    return app.send_static_file("index.html")

# Register blueprints
from threaddit.users.routes import user
from threaddit.subthreads.routes import threads
from threaddit.posts.routes import posts
from threaddit.comments.routes import comments
from threaddit.reactions.routes import reactions
from threaddit.messages.routes import messages

app.register_blueprint(user)
app.register_blueprint(threads)
app.register_blueprint(posts)
app.register_blueprint(comments)
app.register_blueprint(reactions)
app.register_blueprint(messages)

@app.route("/db-test")
def db_test():
    try:
        result = db.engine.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
        tables = [row[0] for row in result]
        return jsonify({"connected": True, "tables": tables})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)})