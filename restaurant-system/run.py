import os
from app import create_app
from app.sockets import socketio

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "8000"))
    socketio.run(app, host="0.0.0.0", port=port, debug=debug)
