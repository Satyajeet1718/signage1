from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory
import os
import json

app = Flask(__name__)

# Configuration
BASE_UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allow only image formats
app.config['BASE_UPLOAD_FOLDER'] = BASE_UPLOAD_FOLDER
app.secret_key = 'your_secret_key'  # Secret key for session management

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_upload_folder(user_id):
    return os.path.join(app.config['BASE_UPLOAD_FOLDER'], user_id)

def load_users():
    with open('users.json', 'r') as file:
        return json.load(file)['users']

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['id']
        password = request.form['password']
        users = load_users()
        for user in users:
            if user['id'] == user_id and user['password'] == password:
                session['user'] = user_id
                os.makedirs(get_user_upload_folder(user_id), exist_ok=True)
                return redirect(url_for('input_page'))
        return render_template('login.html', error='Invalid credentials. Please try again.')
    return render_template('login.html')

# Route for the input page
@app.route('/')
def input_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_id = session['user']
    return render_template('input.html', user_id=user_id)

# Route to handle file upload and display control
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']
    upload_folder = get_user_upload_folder(user_id)

    if 'files' in request.files:
        files = request.files.getlist('files')
        for file in files:
            if file and allowed_file(file.filename):
                filepath = os.path.join(upload_folder, file.filename)
                file.save(filepath)

    if 'display_status' in request.form:
        display_status = request.form['display_status'] == 'on'
        session['display_status'] = display_status

    return redirect(url_for('input_page'))

# API route to get the list of uploaded files
@app.route('/media')
def get_media():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']
    upload_folder = get_user_upload_folder(user_id)
    files = os.listdir(upload_folder)
    return jsonify(files)

# API route to get the display status
@app.route('/status')
def get_status():
    if 'user' not in session:
        return redirect(url_for('login'))
    return jsonify({'status': session.get('display_status', False)})

# API route to delete a specific media file
@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']
    filepath = os.path.join(get_user_upload_folder(user_id), filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'File not found'})

# Route for the display page
@app.route('/display')
def display_page():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']
    return render_template('display.html', user_id=user_id)

# Route for serving images
@app.route('/images/<user_id>/<filename>')
def serve_image(user_id, filename):
    return send_from_directory(get_user_upload_folder(user_id), filename)

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
