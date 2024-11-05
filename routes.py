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

@main.route('/account')
@login_required
def account():
    return render_template('account.html')

@main.route('/upload_voice', methods=['POST'])
@login_required
def upload_voice():
    if 'csv_file' not in request.files:
        flash('No file selected')
        return redirect(url_for('main.account'))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('main.account'))
    
    if file and allowed_file(file.filename):
        try:
            # Read CSV file to validate format
            df = pd.read_csv(file)
            required_columns = ['timestamp', 'text', 'audio_file']
            if not all(col in df.columns for col in required_columns):
                flash('Invalid CSV format. Required columns: timestamp, text, audio_file')
                return redirect(url_for('main.account'))
            
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
            return redirect(url_for('main.account'))
            
        except Exception as e:
            flash('Error processing CSV file')
            return redirect(url_for('main.account'))
    
    flash('Invalid file type. Please upload a CSV file')
    return redirect(url_for('main.account'))
