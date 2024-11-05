import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pandas as pd
from models import VoiceUpload
from app import db
from utils.mail import send_csv_upload_notification
from io import StringIO

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
        flash('No file was uploaded. Please select a CSV file.')
        return redirect(url_for('main.account'))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash('No file selected. Please choose a CSV file to upload.')
        return redirect(url_for('main.account'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Only CSV files are allowed.')
        return redirect(url_for('main.account'))
    
    try:
        # Read and validate CSV file
        file_content = file.read()
        try:
            df = pd.read_csv(StringIO(file_content.decode('utf-8')))
        except UnicodeDecodeError:
            flash('Error: The CSV file must be encoded in UTF-8 format.')
            return redirect(url_for('main.account'))
        except pd.errors.EmptyDataError:
            flash('Error: The uploaded CSV file is empty.')
            return redirect(url_for('main.account'))
        except Exception as e:
            current_app.logger.error(f"CSV parsing error: {str(e)}")
            flash(f'Error parsing CSV file: {str(e)}')
            return redirect(url_for('main.account'))

        # Trim whitespace from column names
        df.columns = df.columns.str.strip()
        
        required_columns = ['full name', 'phone number', 'email']
        present_columns = list(df.columns)
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            flash(f'Invalid CSV format. Missing required columns: {", ".join(missing_columns)}. '
                  f'Found columns: {", ".join(present_columns)}. '
                  f'Required columns are: {", ".join(required_columns)}')
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
        
        # Send email notification with CSV attachment in a separate try-except block
        try:
            email_sent = send_csv_upload_notification(file_content, filename)
            if email_sent:
                voice_upload.status = 'completed'
                flash('Voice data uploaded successfully and notification sent.')
            else:
                voice_upload.status = 'notification_failed'
                flash('Voice data uploaded successfully but notification email failed to send.')
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Email sending error: {str(e)}")
            voice_upload.status = 'notification_failed'
            db.session.commit()
            flash('Voice data uploaded but failed to send notification email.')
        
        return redirect(url_for('main.account'))
            
    except Exception as e:
        current_app.logger.error(f"Upload processing error: {str(e)}")
        flash(f'Error processing upload: {str(e)}')
        return redirect(url_for('main.account'))
