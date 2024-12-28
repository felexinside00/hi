from flask import Flask, request, Response, render_template_string, redirect, url_for, make_response
import uuid
import os
from functools import wraps

app = Flask(__name__)

APPROVAL_FILE = 'approval.txt'

# Generate a unique key
def generate_unique_key():
    return str(uuid.uuid4())

# Read the approval file
def read_approval_file():
    approvals = {}
    if os.path.exists(APPROVAL_FILE):
        with open(APPROVAL_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                if line and ',' in line:
                    key, status = line.split(',', 1)
                    approvals[key] = status
    return approvals

# Write a new key to the approval file
def write_new_key(key):
    with open(APPROVAL_FILE, 'a') as file:
        file.write(f'{key},Pending\n')

# Update the status of a key
def update_key_status(key, new_status):
    approvals = read_approval_file()
    if key in approvals:
        approvals[key] = new_status
        with open(APPROVAL_FILE, 'w') as file:
            for k, status in approvals.items():
                file.write(f'{k},{status}\n')
        return True
    return False

# Home route
@app.route('/')
def home():
    unique_key = generate_unique_key()
    write_new_key(unique_key)
    return render_template_string('''
        <h1>Welcome!</h1>
        <p>Your unique key: <strong>{{ key }}</strong></p>
        <p>Please send this key to the administrator for approval.</p>
    ''', key=unique_key)

# Check status route
@app.route('/check', methods=['GET', 'POST'])
def check_status():
    if request.method == 'POST':
        user_key = request.form['user_key']
        approvals = read_approval_file()
        status = approvals.get(user_key, 'Invalid')
        if status == 'Approved':
            # Set a cookie for lifetime access
            response = make_response(redirect(url_for('welcome')))
            response.set_cookie('approved_user', user_key)
            return response
        elif status == 'Pending':
            return render_template_string('''
                <h1>Pending Approval</h1>
                <p>Your key is still pending approval. Please wait for the administrator to approve it.</p>
            ''')
        else:
            return render_template_string('''
                <h1>Invalid Key</h1>
                <p>The key you entered is invalid. Please check and try again.</p>
            ''')
    return render_template_string('''
        <h1>Check Key Status</h1>
        <form method="post">
            <label for="user_key">Enter your key:</label>
            <input type="text" name="user_key" required>
            <button type="submit">Check Status</button>
        </form>
    ''')

# Welcome page for approved users
@app.route('/welcome')
def welcome():
    approved_user = request.cookies.get('approved_user')
    approvals = read_approval_file()
    if approved_user in approvals and approvals[approved_user] == 'Approved':
        return render_template_string('''
            <h1>Welcome to the Approved Users Area!</h1>
            <p>Click the button below to proceed:</p>
            <form action="http://faizuwardon.kesug.com/" method="get">
                <button type="submit">Go to the Application</button>
            </form>
        ''')
    return redirect(url_for('home'))

# Admin panel
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.authorization:
        username = request.authorization.username
        password = request.authorization.password
        if username == 'admin' and password == 'WARDON_H3R3':
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
    return Response('Access Denied', 401, {'WWW-Authenticate': 'Basic realm="Admin Panel"'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
