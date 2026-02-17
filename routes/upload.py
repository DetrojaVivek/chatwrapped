import os, uuid, json
from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import current_user
from werkzeug.utils import secure_filename
from database.models import Analysis, db
from utils.whatsapp_parser import parse_whatsapp_chat
from utils.stats_calculator import calculate_all_stats

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'txt'}
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@upload_bp.route('/upload', methods=['GET', 'POST'])
def handle_upload():
    if request.method == 'GET':
        return render_template('upload.html')
    
    # Validate file
    if 'file' not in request.files:
        flash('File select karo pehle!', 'error')
        return redirect(url_for('upload.handle_upload'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('upload.handle_upload'))
        
    if not file.filename.lower().endswith('.txt'):
        flash('Sirf .txt file allowed hai', 'error')
        return redirect(url_for('upload.handle_upload'))
    
    chat_name = request.form.get('chat_name', 'My Chat')
    if not chat_name:
        chat_name = 'My Chat'
    chat_name = chat_name[:200]
    
    # Save temporarily with unique name
    unique_name = str(uuid.uuid4()) + '.txt'
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)
    
    try:
        file.save(file_path)
        
        # Parse and analyze
        parsed_messages = parse_whatsapp_chat(file_path)
        
        if len(parsed_messages) < 10:
            os.remove(file_path)
            flash('Chat file mein bahut kam messages hain ya format galat hai.', 'error')
            return redirect(url_for('upload.handle_upload'))
        
        stats = calculate_all_stats(parsed_messages)
        
        # Save to database
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Convert stats to JSON string
        results_json_str = json.dumps(stats, default=str)
        
        analysis = Analysis(
            user_id      = user_id,
            chat_name    = chat_name,
            results_json = results_json_str,
            file_deleted = True
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        # Clean up file immediately
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return redirect(url_for('analysis.show_results', analysis_id=analysis.id))
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        flash(f'Error analyzing chat: {str(e)}', 'error')
        print(f"Error: {e}") # For debugging
        return redirect(url_for('upload.handle_upload'))

@upload_bp.route('/error/invalid')
def invalid_file():
    return render_template('errors/invalid-file.html'), 400

@upload_bp.route('/error/filesize')
def file_too_large():
    return render_template('errors/filesize.html'), 413
