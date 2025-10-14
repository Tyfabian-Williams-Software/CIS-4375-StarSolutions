from flask_socketio import SocketIO, emit

# Create socketio object but delay init_app until app is available.
socketio = SocketIO()


def init_sockets(app, async_mode: str | None = None, **kwargs):
    """Initialize Socket.IO for the given Flask app.

    Pass async_mode (e.g. 'eventlet', 'gevent', 'threading') to force a specific async driver.
    Additional kwargs are forwarded to socketio.init_app.
    """
    if async_mode:
        socketio.init_app(app, async_mode=async_mode, cors_allowed_origins="*", **kwargs)
    else:
        # Let the extension choose a sensible default if no async_mode is provided.
        socketio.init_app(app, cors_allowed_origins="*", **kwargs)


# Example event listeners (they will be registered once init_app is called)
@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")