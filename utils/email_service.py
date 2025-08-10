from flask_mail import Mail, Message
from flask import current_app
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

class EmailService:
    def __init__(self, app=None):
        self.mail = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app"""
        app.config['MAIL_SERVER'] = 'smtp.gmail.com'
        app.config['MAIL_PORT'] = 587
        app.config['MAIL_USE_TLS'] = True
        app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
        app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')
        app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USER')
        
        self.mail = Mail(app)
    
    def send_complaint_notification_to_admin(self, complaint_data, pdf_data, admin_email):
        """Send complaint notification to admin with PDF attachment"""
        try:
            subject = f"New Complaint Submitted - {complaint_data['ticket_id']}"
            
            # HTML email body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                            New Complaint Submitted
                        </h2>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #e74c3c; margin-top: 0;">Complaint Details</h3>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px; font-weight: bold; width: 30%;">Ticket ID:</td>
                                    <td style="padding: 8px;">{complaint_data['ticket_id']}</td>
                                </tr>
                                <tr style="background-color: #ecf0f1;">
                                    <td style="padding: 8px; font-weight: bold;">User:</td>
                                    <td style="padding: 8px;">{complaint_data['user_name']} ({complaint_data['user_email']})</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Title:</td>
                                    <td style="padding: 8px;">{complaint_data['title']}</td>
                                </tr>
                                <tr style="background-color: #ecf0f1;">
                                    <td style="padding: 8px; font-weight: bold;">Category:</td>
                                    <td style="padding: 8px;"><span style="background-color: #3498db; color: white; padding: 2px 8px; border-radius: 3px;">{complaint_data['category']}</span></td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Priority:</td>
                                    <td style="padding: 8px;"><span style="background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px;">{complaint_data['priority']}</span></td>
                                </tr>
                                <tr style="background-color: #ecf0f1;">
                                    <td style="padding: 8px; font-weight: bold;">Status:</td>
                                    <td style="padding: 8px;"><span style="background-color: #f39c12; color: white; padding: 2px 8px; border-radius: 3px;">{complaint_data['status']}</span></td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Created:</td>
                                    <td style="padding: 8px;">{complaint_data['created_at']}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="background-color: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h4 style="color: #2c3e50; margin-top: 0;">Description:</h4>
                            <p style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 0;">
                                {complaint_data['description']}
                            </p>
                        </div>
                        
                        {self._get_attachments_html(complaint_data.get('attachments', []))}
                        
                        <div style="margin-top: 30px; padding: 20px; background-color: #2c3e50; color: white; text-align: center; border-radius: 5px;">
                            <p style="margin: 0;">Please find the detailed complaint ticket attached as PDF.</p>
                            <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
                                This is an automated notification from the Complaint Management System.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Create message
            msg = Message(
                subject=subject,
                recipients=[admin_email],
                html=html_body
            )
            
            # Attach PDF
            msg.attach(
                filename=f"complaint_{complaint_data['ticket_id']}.pdf",
                content_type="application/pdf",
                data=pdf_data
            )
            
            self.mail.send(msg)
            return True
            
        except Exception as e:
            print(f"Error sending admin notification: {str(e)}")
            return False
    
    def send_complaint_confirmation_to_user(self, complaint_data, pdf_data, user_email):
        """Send complaint confirmation to user with PDF attachment"""
        try:
            subject = f"Complaint Submitted Successfully - {complaint_data['ticket_id']}"
            
            # HTML email body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #27ae60; border-bottom: 2px solid #27ae60; padding-bottom: 10px;">
                            Complaint Submitted Successfully
                        </h2>
                        
                        <div style="background-color: #d5f4e6; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #27ae60;">
                            <h3 style="color: #155724; margin-top: 0;">✅ Your complaint has been received!</h3>
                            <p style="margin: 0;">
                                Thank you for submitting your complaint. We have received your request and our team will review it shortly.
                            </p>
                        </div>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #2c3e50; margin-top: 0;">Your Complaint Details</h3>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px; font-weight: bold; width: 30%;">Ticket ID:</td>
                                    <td style="padding: 8px; font-family: monospace; background-color: #e9ecef; border-radius: 3px;">{complaint_data['ticket_id']}</td>
                                </tr>
                                <tr style="background-color: #ecf0f1;">
                                    <td style="padding: 8px; font-weight: bold;">Title:</td>
                                    <td style="padding: 8px;">{complaint_data['title']}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Category:</td>
                                    <td style="padding: 8px;"><span style="background-color: #3498db; color: white; padding: 2px 8px; border-radius: 3px;">{complaint_data['category']}</span></td>
                                </tr>
                                <tr style="background-color: #ecf0f1;">
                                    <td style="padding: 8px; font-weight: bold;">Priority:</td>
                                    <td style="padding: 8px;"><span style="background-color: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px;">{complaint_data['priority']}</span></td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Status:</td>
                                    <td style="padding: 8px;"><span style="background-color: #f39c12; color: white; padding: 2px 8px; border-radius: 3px;">{complaint_data['status']}</span></td>
                                </tr>
                                <tr style="background-color: #ecf0f1;">
                                    <td style="padding: 8px; font-weight: bold;">Submitted:</td>
                                    <td style="padding: 8px;">{complaint_data['created_at']}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; border-left: 4px solid #ffc107;">
                            <h4 style="color: #856404; margin-top: 0;">📋 What happens next?</h4>
                            <ul style="color: #856404; margin: 0; padding-left: 20px;">
                                <li>Our admin team will review your complaint</li>
                                <li>You will receive updates via email</li>
                                <li>Use your Ticket ID <strong>{complaint_data['ticket_id']}</strong> for any follow-ups</li>
                                <li>Expected response time: 24-48 hours</li>
                            </ul>
                        </div>
                        
                        {self._get_attachments_html(complaint_data.get('attachments', []))}
                        
                        <div style="margin-top: 30px; padding: 20px; background-color: #2c3e50; color: white; text-align: center; border-radius: 5px;">
                            <p style="margin: 0;">A detailed copy of your complaint ticket is attached to this email.</p>
                            <p style="margin: 10px 0 0 0; font-size: 12px; opacity: 0.8;">
                                Please keep this email for your records.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Create message
            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=html_body
            )
            
            # Attach PDF
            msg.attach(
                filename=f"complaint_{complaint_data['ticket_id']}.pdf",
                content_type="application/pdf",
                data=pdf_data
            )
            
            self.mail.send(msg)
            return True
            
        except Exception as e:
            print(f"Error sending user confirmation: {str(e)}")
            return False
    
    def send_complaint_update_notification(self, complaint_data, pdf_data, user_email, update_message):
        """Send complaint update notification to user"""
        try:
            subject = f"Complaint Update - {complaint_data['ticket_id']}"
            
            # HTML email body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                            Complaint Status Update
                        </h2>
                        
                        <div style="background-color: #d1ecf1; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #3498db;">
                            <h3 style="color: #0c5460; margin-top: 0;">📢 Update on your complaint</h3>
                            <p style="margin: 0;">
                                There has been an update to your complaint <strong>{complaint_data['ticket_id']}</strong>.
                            </p>
                        </div>
                        
                        <div style="background-color: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h4 style="color: #2c3e50; margin-top: 0;">Update Message:</h4>
                            <p style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 0;">
                                {update_message}
                            </p>
                        </div>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #2c3e50; margin-top: 0;">Current Status</h3>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px; font-weight: bold; width: 30%;">Ticket ID:</td>
                                    <td style="padding: 8px; font-family: monospace; background-color: #e9ecef; border-radius: 3px;">{complaint_data['ticket_id']}</td>
                                </tr>
                                <tr style="background-color: #ecf0f1;">
                                    <td style="padding: 8px; font-weight: bold;">Status:</td>
                                    <td style="padding: 8px;"><span style="background-color: #28a745; color: white; padding: 2px 8px; border-radius: 3px;">{complaint_data['status']}</span></td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Last Updated:</td>
                                    <td style="padding: 8px;">{complaint_data['updated_at']}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="margin-top: 30px; padding: 20px; background-color: #2c3e50; color: white; text-align: center; border-radius: 5px;">
                            <p style="margin: 0;">Updated complaint details are attached as PDF.</p>
                            <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
                                Thank you for your patience.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Create message
            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=html_body
            )
            
            # Attach PDF
            msg.attach(
                filename=f"complaint_{complaint_data['ticket_id']}_updated.pdf",
                content_type="application/pdf",
                data=pdf_data
            )
            
            self.mail.send(msg)
            return True
            
        except Exception as e:
            print(f"Error sending update notification: {str(e)}")
            return False
    
    def send_welcome_email(self, recipient_email, recipient_name, user_type, role=None):
        """Send welcome email to new users/admins"""
        try:
            if user_type == "admin":
                subject = "Welcome to CMS - Admin Account Created"
                html_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">
                                Welcome to Complaint Management System
                            </h2>
                            
                            <div style="background-color: #f8d7da; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #e74c3c;">
                                <h3 style="color: #721c24; margin-top: 0;">🛡️ Admin Account Created</h3>
                                <p style="margin: 0;">
                                    Hello <strong>{recipient_name}</strong>, your admin account has been successfully created.
                                </p>
                            </div>
                            
                            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                                <h4 style="color: #2c3e50; margin-top: 0;">Admin Responsibilities:</h4>
                                <ul style="margin: 0; padding-left: 20px;">
                                    <li>Review and manage user complaints</li>
                                    <li>Update complaint status and provide responses</li>
                                    <li>Monitor system statistics and performance</li>
                                    <li>Ensure timely resolution of issues</li>
                                </ul>
                            </div>
                            
                            <div style="margin-top: 30px; padding: 20px; background-color: #2c3e50; color: white; text-align: center; border-radius: 5px;">
                                <p style="margin: 0;">You can now log in to the admin panel and start managing complaints.</p>
                            </div>
                        </div>
                    </body>
                </html>
                """
            else:
                subject = "Welcome to CMS - Account Created"
                role_display = role.title() if role else "User"
                html_body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #2c3e50; border-bottom: 2px solid #27ae60; padding-bottom: 10px;">
                                Welcome to Complaint Management System
                            </h2>
                            
                            <div style="background-color: #d5f4e6; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #27ae60;">
                                <h3 style="color: #155724; margin-top: 0;">🎉 Account Created Successfully</h3>
                                <p style="margin: 0;">
                                    Hello <strong>{recipient_name}</strong>, welcome to our Complaint Management System! Your {role_display} account has been created.
                                </p>
                            </div>
                            
                            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                                <h4 style="color: #2c3e50; margin-top: 0;">What you can do:</h4>
                                <ul style="margin: 0; padding-left: 20px;">
                                    <li>Submit complaints with detailed descriptions</li>
                                    <li>Upload supporting documents and images</li>
                                    <li>Track the status of your complaints</li>
                                    <li>Receive email updates on progress</li>
                                    <li>Download complaint tickets as PDF</li>
                                </ul>
                            </div>
                            
                            <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0;">
                                <h4 style="color: #856404; margin-top: 0;">📋 Getting Started:</h4>
                                <p style="color: #856404; margin: 0;">
                                    Log in to your account and start submitting complaints. Our team is here to help resolve your issues quickly and efficiently.
                                </p>
                            </div>
                            
                            <div style="margin-top: 30px; padding: 20px; background-color: #2c3e50; color: white; text-align: center; border-radius: 5px;">
                                <p style="margin: 0;">Thank you for joining our platform!</p>
                            </div>
                        </div>
                    </body>
                </html>
                """
            
            # Create message
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                html=html_body
            )
            
            self.mail.send(msg)
            return True, "Welcome email sent successfully"
            
        except Exception as e:
            error_msg = f"Error sending welcome email: {str(e)}"
            print(error_msg)
            return False, error_msg

    def _get_attachments_html(self, attachments):
        """Generate HTML for attachments section"""
        if not attachments:
            return ""
        
        html = """
        <div style="background-color: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 20px;">
            <h4 style="color: #2c3e50; margin-top: 0;">Attachments:</h4>
            <ul style="margin: 0; padding-left: 20px;">
        """
        
        for attachment in attachments:
            html += f"""
                <li style="margin-bottom: 5px;">
                    <a href="{attachment['file_url']}" style="color: #3498db; text-decoration: none;">
                        📎 {attachment['original_filename']}
                    </a>
                    <span style="color: #7f8c8d; font-size: 12px; margin-left: 10px;">
                        ({attachment['file_type']}, {self._format_file_size(attachment['file_size'])})
                    </span>
                </li>
            """
        
        html += """
            </ul>
        </div>
        """
        return html
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def send_feedback_notification(self, complaint, feedback):
        """Send feedback notification to admin"""
        try:
            subject = f"Feedback Received - {complaint.ticket_id}"
            
            # Generate star rating HTML
            stars_html = ""
            for i in range(1, 6):
                if i <= feedback.rating:
                    stars_html += "⭐"
                else:
                    stars_html += "☆"
            
            # HTML email body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                            Feedback Received
                        </h2>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="color: #27ae60; margin-top: 0;">Complaint Details</h3>
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="padding: 8px; font-weight: bold; width: 30%;">Ticket ID:</td>
                                    <td style="padding: 8px;">{complaint.ticket_id}</td>
                                </tr>
                                <tr style="background-color: #ecf0f1;">
                                    <td style="padding: 8px; font-weight: bold;">User:</td>
                                    <td style="padding: 8px;">{complaint.user.name} ({complaint.user.email})</td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Title:</td>
                                    <td style="padding: 8px;">{complaint.title}</td>
                                </tr>
                                <tr style="background-color: #ecf0f1;">
                                    <td style="padding: 8px; font-weight: bold;">Category:</td>
                                    <td style="padding: 8px;"><span style="background-color: #3498db; color: white; padding: 2px 8px; border-radius: 3px;">{complaint.category.value}</span></td>
                                </tr>
                                <tr>
                                    <td style="padding: 8px; font-weight: bold;">Status:</td>
                                    <td style="padding: 8px;"><span style="background-color: #27ae60; color: white; padding: 2px 8px; border-radius: 3px;">{complaint.status.value}</span></td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="background-color: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin: 20px 0;">
                            <h4 style="color: #2c3e50; margin-top: 0;">User Feedback</h4>
                            <div style="text-align: center; margin: 20px 0;">
                                <div style="font-size: 24px; margin-bottom: 10px;">
                                    {stars_html}
                                </div>
                                <div style="font-size: 18px; font-weight: bold; color: #2c3e50;">
                                    {feedback.rating}/5 Stars
                                </div>
                            </div>
                            {f'<p style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 0;"><strong>Comment:</strong> {feedback.feedback_text}</p>' if feedback.feedback_text else ''}
                        </div>
                        
                        <div style="margin-top: 30px; padding: 20px; background-color: #2c3e50; color: white; text-align: center; border-radius: 5px;">
                            <p style="margin: 0;">Thank you for your service! This feedback helps improve our complaint resolution process.</p>
                            <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">
                                This is an automated notification from the Complaint Management System.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Get admin email from environment or use default
            admin_email = os.getenv('ADMIN_EMAIL', os.getenv('EMAIL_USER'))
            
            # Create message
            msg = Message(
                subject=subject,
                recipients=[admin_email],
                html=html_body
            )
            
            # Send email
            self.mail.send(msg)
            return True, "Feedback notification sent successfully"
            
        except Exception as e:
            print(f"Error sending feedback notification: {str(e)}")
            return False, f"Failed to send feedback notification: {str(e)}"

# Global email service instance
email_service = EmailService()