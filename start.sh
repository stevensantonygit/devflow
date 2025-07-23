# Start the Flask app with gunicorn
gunicorn app:app --host 0.0.0.0 --port ${PORT:-5000} --workers 1