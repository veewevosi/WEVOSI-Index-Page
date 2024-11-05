import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from flask import render_template, current_app

def send_verification_email(user, verification_url):
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    
    # Render the HTML template
    html_content = render_template('email/verification.html',
                                 username=user.username,
                                 verification_url=verification_url)
    
    message = Mail(
        from_email=Email('noreply@wevosi.com', 'WEVOSI'),
        to_emails=To(user.email),
        subject='Verify Your WEVOSI Account',
        html_content=HtmlContent(html_content)
    )
    
    try:
        response = sg.send(message)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send verification email: {str(e)}")
        return False
