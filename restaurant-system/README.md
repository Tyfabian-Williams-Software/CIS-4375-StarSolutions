# CIS-4375-StarSolutions
This is the current state of our project's repo

## Setup & Running

- Copy `.env.example` to `.env` and fill in `SECRET_KEY` and `DATABASE_URL` with your local credentials. Do not commit `.env`.
- Create a virtual environment and install dependencies: `pip install -r requirements.txt`.
- To run locally with sockets: `python run.py` (this uses Flask-SocketIO). If using `eventlet`, install it and the server will pick it up.

Security: remove any hard-coded credentials from source. The repository now contains `.env.example` and `.gitignore` to help with this.
