import os
import sys

# Ensure project root is on sys.path so `import app` works when running this script directly
try:
    script_dir = os.path.dirname(__file__)
except NameError:
    # __file__ is not defined when the script is exec()'d; fall back to cwd
    script_dir = os.getcwd()

project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

from app import create_app, db
from werkzeug.security import generate_password_hash
from app.models import User

# Allow overriding via env; default to local sqlite file
os.environ.setdefault('DATABASE_URL', 'sqlite:///./.local_admin.db')

username = sys.argv[1] if len(sys.argv) > 1 else 'bootstrap_admin'
password = sys.argv[2] if len(sys.argv) > 2 else 'AdminS3cret!'
role = sys.argv[3] if len(sys.argv) > 3 else 'admin'

app = create_app()
with app.app_context():
    db.create_all()
    existing = User.query.filter_by(username=username).first()
    if existing:
        print('User already exists:', username)
    else:
        u = User(username=username, password=generate_password_hash(password), role=role)
        db.session.add(u)
        db.session.commit()
        print('created', u.username)
