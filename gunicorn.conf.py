import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

workers = int(
    os.environ.get(
        "WEB_CONCURRENCY",
        "2"
    )
)

worker_class = "sync"

timeout = 90
graceful_timeout = 20
keepalive = 5

max_requests = 500
max_requests_jitter = 50

accesslog = "-"
errorlog = "-"
loglevel = "info"

capture_output = True