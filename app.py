import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
bcrypt = Bcrypt()
login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import routes after app initialization
with app.app_context():
    from routes import main
    from auth import auth_bp
    
    app.register_blueprint(main)
    app.register_blueprint(auth_bp)
    
    import models
    db.create_all()
