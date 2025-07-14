"""
Flask wrapper for Django FinSplit application.
This allows deployment using the Flask deployment service.
"""
import os
import sys
import subprocess
from flask import Flask, request, Response
import requests
from threading import Thread
import time

app = Flask(__name__)

# Global variable to track Django server
django_process = None

def start_django_server():
    """Start Django development server in background."""
    global django_process
    try:
        # Change to the Django project directory
        os.chdir('/home/ubuntu/FinSplit')
        
        # Start Django server
        django_process = subprocess.Popen([
            'python3.11', 'manage.py', 'runserver', '127.0.0.1:8001'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        print("Django server started on port 8001")
        
    except Exception as e:
        print(f"Error starting Django server: {e}")

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_to_django(path):
    """Proxy all requests to Django server."""
    try:
        # Construct the Django URL
        django_url = f"http://127.0.0.1:8001/{path}"
        
        # Forward the request to Django
        if request.method == 'GET':
            resp = requests.get(django_url, params=request.args, headers=dict(request.headers))
        elif request.method == 'POST':
            resp = requests.post(django_url, data=request.form, files=request.files, headers=dict(request.headers))
        elif request.method == 'PUT':
            resp = requests.put(django_url, data=request.get_data(), headers=dict(request.headers))
        elif request.method == 'DELETE':
            resp = requests.delete(django_url, headers=dict(request.headers))
        elif request.method == 'PATCH':
            resp = requests.patch(django_url, data=request.get_data(), headers=dict(request.headers))
        
        # Return the response from Django
        return Response(
            resp.content,
            status=resp.status_code,
            headers=dict(resp.headers)
        )
        
    except requests.exceptions.ConnectionError:
        return "Django server is not running", 503
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    # Start Django server in background
    django_thread = Thread(target=start_django_server)
    django_thread.daemon = True
    django_thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)

