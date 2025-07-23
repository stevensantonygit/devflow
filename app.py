from flask import Flask, render_template, request, jsonify
import subprocess
import sys
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_command():
    try:
        command = request.json.get('command', '')
        if not command.startswith('devflow'):
            command = f'devflow {command}'
        
        # Replace devflow with python devflow.py
        command = command.replace('devflow', 'python devflow.py', 1)
        
        # Run the command
        result = subprocess.run(
            command.split(), 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        return jsonify({
            'output': result.stdout + result.stderr,
            'success': result.returncode == 0
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            'output': 'Command timed out after 30 seconds',
            'success': False
        })
    except Exception as e:
        return jsonify({
            'output': f'Error: {str(e)}',
            'success': False
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)