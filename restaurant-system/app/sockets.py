from flask_socketio import SocketIO, emit
import logging

# Create socketio object but delay init_app until app is available.
socketio = SocketIO()


def _choose_async_mode(preferred: str | None = None) -> str:
    """Choose an async mode for python-socketio/engineio.

    Preference order when preferred is None: eventlet, gevent, threading.
    Returns the chosen async_mode string.
    """
    if preferred:
        return preferred

    # Try eventlet first (preferred for production when available and compatible).
    # Instead of only testing `import eventlet`, ensure engineio's eventlet async
    # driver module can be imported too; that will expose runtime incompatibilities
    # such as the missing `start_joinable_thread` on newer Python versions.
    try:
        import importlib
        importlib.import_module("engineio.async_drivers.eventlet")
        return "eventlet"
    except Exception:
        # eventlet not usable; try gevent
        pass

    # Try gevent next, checking engineio's gevent driver module.
    try:
        import importlib
        importlib.import_module("engineio.async_drivers.gevent")
        return "gevent"
    except Exception:
        pass

    # Fallback to threading (safe default)
    return "threading"


def init_sockets(app, async_mode: str | None = None, **kwargs):
    """Initialize Socket.IO for the given Flask app.

    This function will attempt to select a production-appropriate async driver
    (eventlet -> gevent -> threading) unless `async_mode` is explicitly passed.
    It logs the chosen driver so operators can adjust their environment if needed.
    """
    chosen = _choose_async_mode(async_mode)

    # If eventlet is chosen, it's common to call eventlet.monkey_patch() early
    # in the process. We won't monkey-patch here automatically because that can
    # have surprising side-effects; document in README instead. If the user has
    # installed eventlet and wishes to use it, they should ensure it's compatible
    # with their Python version (eventlet historically lags latest Python).
    logging.getLogger(__name__).info("SocketIO async_mode selected: %s", chosen)

    # Initialize the socketio extension with the chosen async mode.
    socketio.init_app(app, async_mode=chosen, cors_allowed_origins="*", **kwargs)


# Example event listeners (they will be registered once init_app is called)
@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")