"""
Gunicorn Configuration for IT Due Diligence Agent

Production WSGI server configuration.
"""

import os
import multiprocessing

# Bind to port from environment or default to 8080
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Workers - MEMORY FIX: reduced from 2 to 1 to lower baseline memory footprint
# Analysis pipeline is memory-intensive, not I/O bound
workers = int(os.environ.get('GUNICORN_WORKERS', '1'))

# Threads per worker - MEMORY FIX: reduced from 4 to 2
# Each thread can handle concurrent requests; fewer threads = lower memory usage
threads = int(os.environ.get('GUNICORN_THREADS', '2'))

# Worker class - sync is fine for Flask, use gevent for async
worker_class = 'sync'

# Timeout - 5 minutes for long-running analysis
timeout = 300

# Keep-alive connections
keepalive = 2

# Logging
errorlog = '-'  # stderr
accesslog = '-'  # stdout
loglevel = os.environ.get('LOG_LEVEL', 'info')

# Capture output from application
capture_output = True

# Graceful timeout for worker restart
graceful_timeout = 30

# Max requests before worker restart (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Preload app for faster worker startup (but careful with shared state)
preload_app = False

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Process naming
proc_name = 'it-diligence-agent'

# SSL (handled by Railway/nginx in production)
keyfile = None
certfile = None
