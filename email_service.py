# email_service.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer
from flask import url_for

# Configuration (you should set these as environment variables in production)
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME', 'your-email@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your-app-password')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Initialize serializer for generating tokens
serializer = URLSafeTimedSerializer(SECRET_KEY)

def send_verification_email(user_email, user_id, username):
    """Send email verification link to user"""
    try:
        # Generate verification token
        token = serializer.dumps(user_email, salt='email-verification')
        
        # Create verification URL
        verification_url = url_for('verify_email', token=token, _external=True)
        
        # Create email content
        subject = "Verify Your Email Address"
        html_content = f"""
        <html>
            <body>
                <h2>Email Verification</h2>
                <p>Hello {username},</p>
                <p>Please click the link below to verify your email address:</p>
                <p><a href="{verification_url}">{verification_url}</a></p>
                <p>If you didn't create an account with us, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Money & Event Manager Team</p>
            </body>
        </html>
        """
        
        text_content = f"""
        Email Verification
        Hello {username},
        Please click the link below to verify your email address:
        {verification_url}
        If you didn't create an account with us, please ignore this email.
        Best regards,
        Money & Event Manager Team
        """
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USERNAME
        msg['To'] = user_email
        
        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def verify_token(token, expiration=3600):
    """Verify the email verification token"""
    try:
        email = serializer.loads(
            token,
            salt='email-verification',
            max_age=expiration
        )
        return email
    except:
        return None