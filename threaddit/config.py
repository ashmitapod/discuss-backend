import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URI = os.getenv('DATABASE_URL')  # Neon Postgres URL
if DATABASE_URI and DATABASE_URI.startswith("postgres://"):
    DATABASE_URI = DATABASE_URI.replace("postgres://", "postgresql://", 1)

# Security
SECRET_KEY = os.getenv('SECRET_KEY')

# Cloudinary
CLOUDINARY_NAME = os.getenv('CLOUDINARY_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')