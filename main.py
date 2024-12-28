from flask import Flask, request, Response, render_template_string, redirect, url_for, make_response
import uuid
import os
from functools import wraps

app = Flask(__name__)

# Path to the approval file
APPROVAL_FILE = 'approval.txt'

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'WARDON_H3R3'

# Authentication functions
def check_auth(username, password):
    """Verify if the provided username and password are correct."""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def authenticate():
    """Send a 401 response to prompt for basic authentication."""
    return Response(
        'Access denied: Please provide valid credentials.', 401,
        {'WWW-Authenticate': 'Basic realm="Admin Panel"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Generate a unique key for the user
def generate_unique_key():
    return str(uuid.uuid4())

# Read approval statuses from the file
def read_approval_file():
    approvals = {}
    if os.path.exists(APPROVAL_FILE):
        with open(APPROVAL_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                if line and ',' in line:  # Skip empty lines
                    key, status = line.split(',', 1)
                    approvals[key] = status
    return approvals

# Write a new key with 'Pending' status to the file
def write_new_key(key):
    with open(APPROVAL_FILE, 'a') as file:
        file.write(f'{key},Pending\n')

# Update the status of a key in the approval file
def update_key_status(key, new_status):
    approvals = read_approval_file()
    if key in approvals:
        approvals[key] = new_status
        with open(APPROVAL_FILE, 'w') as file:
            for k, status in approvals.items():
                file.write(f'{k},{status}\n')
        return True
    return False

# Home route to generate and display a unique key
@app.route('/')
def home():
    unique_key = request.cookies.get('unique_key')
    if not unique_key:
        unique_key = generate_unique_key()
        write_new_key(unique_key)

    resp = make_response(render_template_string('''
        <h1>Welcome!</h1>
        <p>Your unique key: <strong>{{ key }}</strong></p>
        <p>Please send this key to the administrator for approval.</p>
    ''', key=unique_key))
    resp.set_cookie('unique_key', unique_key)
    return resp

# Route for the user to check the status of their key
@app.route('/check', methods=['GET', 'POST'])
def check_status():
    if request.method == 'POST':
        user_key = request.form['user_key']
        approvals = read_approval_file()
        status = approvals.get(user_key, 'Invalid')
        if status == 'Approved':
            return render_template_string('''
                <h1>Access Granted</h1>
                <p>Your key has been approved. You can now access the application.</p>
            ''')
        elif status == 'Pending':
            return render_template_string('''
                <h1>Your key is still pending approval</h1>
                <p>Your key is pending approval. Please wait for the administrator to approve it.</p>
            ''')
        else:
            return render_template_string('''
                <h1>Invalid Key</h1>
                <p>The key you entered is invalid. Please check the key and try again.</p>
            ''')
    return render_template_string('''
        <h1>Check Key Status</h1>
        <form method="post">
            <label for="user_key">Enter your key:</label>
            <input type="text" name="user_key" required>
            <button type="submit">Check Status</button>
        </form>
    ''')

# Admin panel route to view and update key statuses
@app.route('/admin', methods=['GET', 'POST'])
@requires_auth
def admin():
    approvals = read_approval_file()
    if request.method == 'POST':
        user_key = request.form['user_key']
        action = request.form['action']
        if action == 'approve':
            success = update_key_status(user_key, 'Approved')
        elif action == 'reject':
            success = update_key_status(user_key, 'Rejected')
        else:
            success = False
        if success:
            message = f'Key {user_key} has been {action}d.'
        else:
            message = f'Key {user_key} not found.'
        return render_template_string('''
            <h1>Admin Panel</h1>
            <p>{{ message }}</p>
            <a href="/admin">Go back</a>
        ''', message=message)

    return render_template_string('''
        <h1>Admin Panel</h1>
        <table border="1">
            <tr>
                <th>Key</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
            {% for key, status in approvals.items() %}
            <tr>
                <td>{{ key }}</td>
                <td>{{ status }}</td>
                <td>
                    {% if status == 'Pending' %}
                    <form method="post" style="display:inline;">
                        <input type="hidden" name="user_key" value="{{ key }}">
                        <input type="hidden" name="action" value="approve">
                        <button type="submit">Approve</button>
                    </form>
                    <form method="post" style="display:inline;">
                        <input type="hidden" name="user_key" value="{{ key }}">
                        <input type="hidden" name="action" value="reject">
                        <button type="submit">Reject</button>
                    </form>
                    {% else %}
                    <span>{{ status }}</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    ''', approvals=approvals)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

