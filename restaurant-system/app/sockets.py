from flask_socketio import SocketIO, emit

socketio = SocketIO(cors_allowed_origins="*")

def init_sockets(app):
    socketio.init_app(app)

# Example event listener (not mandatory)
@socketio.on("connect")
def handle_connect():
    print("Client connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")