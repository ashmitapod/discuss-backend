import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from marshmallow import ValidationError
import cloudinary
from flask_login import LoginManager

# Import config with fallback to environment variables
try:
    from threaddit.config import (
        DATABASE_URI,
        SECRET_KEY,
        CLOUDINARY_API_SECRET,
        CLOUDINARY_API_KEY,
        CLOUDINARY_NAME,
    )
except ImportError:
    # Fallback to environment variables if config file is missing
    DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_NAME = os.environ.get('CLOUDINARY_NAME')

app = Flask(__name__)

# CORS Configuration - Updated for production
# Allow multiple origins for development and production
CORS(app,
     resources={
         r"/api/*": {
             "origins": [
                 "https://discuss-frontend.vercel.app",
                 "https://*.vercel.app",
                 "http://localhost:5173",
                 "http://localhost:5174"
             ],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
             "supports_credentials": True
         }
     })

# Cloudinary config (only if credentials are available)
if CLOUDINARY_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
    )

# Flask app config with environment variable fallbacks
app.config["CLOUDINARY_NAME"] = CLOUDINARY_NAME

# CRITICAL: Database URI configuration with fallbacks
database_uri = DATABASE_URI or os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')

# Handle postgres:// to postgresql:// conversion for newer SQLAlchemy
if database_uri and database_uri.startswith('postgres://'):
    database_uri = database_uri.replace('postgres://', 'postgresql://', 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SECRET_KEY"] = SECRET_KEY or os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Disable to save memory

# Add SQLAlchemy engine options for better Neon compatibility
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "connect_args": {
        "connect_timeout": 10,
        "application_name": "discuss-app"
    }
}

# Production optimizations
if os.environ.get('FLASK_ENV') == 'production':
    app.config["DEBUG"] = False
    app.config["TESTING"] = False
else:
    app.config["DEBUG"] = True

# Validate critical configuration
if not app.config["SQLALCHEMY_DATABASE_URI"]:
    raise RuntimeError("SQLALCHEMY_DATABASE_URI must be set. Check your environment variables or config file.")

# Init extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
ma = Marshmallow(app)

@login_manager.unauthorized_handler
def callback():
    return jsonify({"message": "Unauthorized"}), 401

# Health check endpoint for monitoring
@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "environment": os.environ.get('FLASK_ENV', 'development'),
        "database_configured": bool(app.config.get("SQLALCHEMY_DATABASE_URI"))
    }), 200

# API status endpoint
@app.route("/api/status")
def api_status():
    try:
        # Test database connection
        with db.engine.connect() as connection:
            connection.execute(db.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return jsonify({
        "api": "online",
        "version": "1.0",
        "database": db_status
    }), 200

@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify({"errors": err.messages}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500

# Database test endpoint (remove in production if not needed)
@app.route("/db-test")
def db_test():
    try:
        # Updated for newer SQLAlchemy versions
        with db.engine.connect() as connection:
            result = connection.execute(db.text("SELECT tablename FROM pg_tables WHERE schemaname = 'public';"))
            tables = [row[0] for row in result]
        return jsonify({"connected": True, "tables": tables})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)}), 500

# Register blueprints
from threaddit.users.routes import user
from threaddit.subthreads.routes import threads   
from threaddit.posts.routes import posts
from threaddit.comments.routes import comments
from threaddit.reactions.routes import reactions
from threaddit.messages.routes import messages

app.register_blueprint(user, url_prefix='/api')
app.register_blueprint(threads, url_prefix='/api')
app.register_blueprint(posts, url_prefix='/api')
app.register_blueprint(comments, url_prefix='/api')
app.register_blueprint(reactions, url_prefix='/api')
app.register_blueprint(messages, url_prefix='/api')