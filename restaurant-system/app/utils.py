from app.models import User
from werkzeug.security import generate_password_hash

def create_user(username, password, role):
    user = User(username=username, password=generate_password_hash(password), role=role)
    return user