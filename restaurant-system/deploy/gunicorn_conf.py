# Gunicorn config for the restaurant-system app
# Adjust worker_class to 'eventlet' or 'gevent' depending on the chosen async driver.
# Recommended: use eventlet with Python 3.11 or gevent if you need newer Python support.
import multiprocessing

workers = 2
threads = 2
worker_class = 'eventlet'  # or 'gevent'
bind = '0.0.0.0:8000'
backlog = 2048
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Graceful timeout
timeout = 30

# Logging (optional)
accesslog = '-'
errorlog = '-'
loglevel = 'info'
