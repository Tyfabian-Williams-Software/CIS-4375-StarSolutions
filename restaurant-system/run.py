from app import create_app, socketio, db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # for quick start; later use flask-migrate
    socketio.run(app, host="0.0.0.0", port=5000)