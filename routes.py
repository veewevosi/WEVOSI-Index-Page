import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
from models import VoiceUpload
from app import db

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main.route('/upload_voice', methods=['POST'])
@login_required
def upload_voice():
    if 'csv_file' not in request.files:
        flash('No file selected')
        return redirect(url_for('main.profile'))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('main.profile'))
    
    if file and allowed_file(file.filename):
        try:
            # Read CSV file to validate format
            df = pd.read_csv(file)
            required_columns = ['timestamp', 'text', 'audio_file']
            if not all(col in df.columns for col in required_columns):
                flash('Invalid CSV format. Required columns: timestamp, text, audio_file')
                return redirect(url_for('main.profile'))
            
            filename = secure_filename(file.filename)
            
            # Save upload record to database
            voice_upload = VoiceUpload(
                filename=filename,
                user_id=current_user.id,
                status='pending'
            )
            db.session.add(voice_upload)
            db.session.commit()
            
            flash('Voice data uploaded successfully')
            return redirect(url_for('main.profile'))
            
        except Exception as e:
            flash('Error processing CSV file')
            return redirect(url_for('main.profile'))
    
    flash('Invalid file type. Please upload a CSV file')
    return redirect(url_for('main.profile'))
