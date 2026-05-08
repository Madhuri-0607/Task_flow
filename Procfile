release: python init_db.py
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --worker-class sync --worker-connections 1000 --timeout 120 --access-logfile - --error-logfile - --log-level info
