import os
from flask import Flask, render_template, request, send_file, redirect, url_for, make_response
from steganography import encode_message, decode_message
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'} 

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hide', methods=['POST'])
def hide_message():
    if request.method == 'POST':
        
        if 'image' not in request.files:
            return "Error: No image part"

        file = request.files['image']

       
        if file.filename == '':
            return "Error: No selected image"

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)

            message_to_hide = request.form.get('message')
            if not message_to_hide:
                return "Error: No message to hide"

            encrypted = request.form.get('encrypt') == 'on'
            password = request.form.get('password') or None
            preserve_quality = request.form.get('preserve_quality') == 'on'

            try:
                encoded_image_path = encode_message(image_path, message_to_hide, 'static/uploads/encoded_image.png', encrypted, password, preserve_quality) 
                if encoded_image_path:
                    return send_file(encoded_image_path, as_attachment=True, download_name='encoded_image.png') 
                else:
                    return "Error during message encoding."
            except Exception as e:
                os.remove(image_path) 
                return f"Error during message encoding: {str(e)}"
            finally:
                os.remove(image_path) 


        else:
            return "Error: Allowed image types are: png, jpg, jpeg"
    return redirect(url_for('index')) 

@app.route('/extract', methods=['POST'])
def extract_message():
    if request.method == 'POST':
        if 'image' not in request.files:
            return "Error: No image part"

        file = request.files['image']

        if file.filename == '':
            return "Error: No selected image"

        if file and allowed_file(file.filename):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(image_path)

            is_encrypted = request.form.get('is_encrypted') == 'on'
            password = request.form.get('password') or None

            try:
                extracted_message_text = decode_message(image_path, is_encrypted, password)
                os.remove(image_path) 

                if extracted_message_text:
                    return extracted_message_text 
                else:
                    return "No message extracted or incorrect password."
            except Exception as e:
                os.remove(image_path) 
                return f"Error during message extraction: {str(e)}"

        else:
            return "Error: Allowed image types are: png, jpg, jpeg"

    return redirect(url_for('index')) 


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True) 
    app.run(debug=True)

