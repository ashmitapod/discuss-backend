import os

# Try to load .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (production environment)
    pass

# Database
DATABASE_URI = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI')
if DATABASE_URI and DATABASE_URI.startswith("postgres://"):
    DATABASE_URI = DATABASE_URI.replace("postgres://", "postgresql://", 1)

# Security
SECRET_KEY = os.getenv('SECRET_KEY')

# Cloudinary
CLOUDINARY_NAME = os.getenv('CLOUDINARY_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')