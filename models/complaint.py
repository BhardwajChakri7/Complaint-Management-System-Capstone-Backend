from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum
from .user import db

class ComplaintStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class ComplaintCategory(enum.Enum):
    TECHNICAL = "Technical"
    ACADEMIC = "Academic"
    HOSTEL_MESS = "Hostel/Mess"
    MAINTENANCE = "Maintenance"

class ComplaintPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Complaint(db.Model):
    __tablename__ = 'complaints'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(ComplaintCategory), nullable=False)
    priority = db.Column(db.Enum(ComplaintPriority), nullable=False)
    status = db.Column(db.Enum(ComplaintStatus), default=ComplaintStatus.PENDING)
    
    # File attachments
    attachments = db.relationship('ComplaintAttachment', backref='complaint', lazy=True, cascade='all, delete-orphan')
    
    # Feedback relationship
    feedback = db.relationship('ComplaintFeedback', backref='complaint', uselist=False, lazy=True, cascade='all, delete-orphan')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Admin response
    admin_response = db.Column(db.Text, nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='complaints')
    admin = db.relationship('Admin', backref='handled_complaints')
    
    def __init__(self, user_id, title, description, category, priority):
        self.user_id = user_id
        self.title = title
        self.description = description
        self.category = ComplaintCategory(category)
        self.priority = ComplaintPriority(priority)
        self.ticket_id = self.generate_ticket_id()
    
    def generate_ticket_id(self):
        """Generate unique ticket ID"""
        import random
        import string
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"CMP{timestamp}{random_part}"
    
    def to_dict(self):
        """Convert complaint object to dictionary"""
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'attachments': [att.to_dict() for att in self.attachments],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'admin_response': self.admin_response,
            'admin_id': self.admin_id,
            'feedback': self.feedback.to_dict() if self.feedback else None
        }
    
    def __repr__(self):
        return f'<Complaint {self.ticket_id}>'

class ComplaintAttachment(db.Model):
    __tablename__ = 'complaint_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)  # Cloudinary URL
    file_type = db.Column(db.String(50), nullable=False)  # image, document, etc.
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    cloudinary_public_id = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert attachment object to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_url': self.file_url,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ComplaintAttachment {self.filename}>'

class ComplaintFeedback(db.Model):
    __tablename__ = 'complaint_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False, unique=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    feedback_text = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, complaint_id, rating, feedback_text=None):
        self.complaint_id = complaint_id
        self.rating = rating
        self.feedback_text = feedback_text
    
    def to_dict(self):
        """Convert feedback object to dictionary"""
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'rating': self.rating,
            'feedback_text': self.feedback_text,
            'submitted_at': self.submitted_at.isoformat()
        }
    
    def __repr__(self):
        return f'<ComplaintFeedback {self.complaint_id}>'