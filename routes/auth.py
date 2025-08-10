from flask import Blueprint, request, jsonify
from models.user import User, db, RoleType
from marshmallow import Schema, fields, ValidationError, validate
from utils.email_service import EmailService
import jwt
import os
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

class UserSignupSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(required=True, validate=validate.OneOf(['student', 'faculty']))

signup_schema = UserSignupSchema()

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User signup endpoint"""
    try:
        # Validate request data
        data = signup_schema.load(request.json)
    except ValidationError as err:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': err.messages
        }), 400
    
    try:
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'User with this email already exists'
            }), 409
        
        # Create new user
        new_user = User(
            name=data['name'],
            email=data['email'],
            password=data['password'],
            role=data['role']
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT token
        jwt_secret = os.getenv('JWT_TOKEN')
        if not jwt_secret:
            return jsonify({
                'success': False,
                'message': 'Server configuration error'
            }), 500
            
        token = jwt.encode({
            'user_id': new_user.id,
            'email': new_user.email,
            'role': new_user.role.value,
            'exp': datetime.utcnow() + timedelta(days=7)
        }, jwt_secret, algorithm='HS256')
        
        # Send welcome email
        email_service = EmailService()
        email_sent, email_message = email_service.send_welcome_email(
            recipient_email=new_user.email,
            recipient_name=new_user.name,
            user_type="user",
            role=new_user.role.value
        )
        
        response_data = {
            'user': new_user.to_dict(),
            'token': token
        }
        
        # Add email status to response
        if email_sent:
            response_message = 'User created successfully and welcome email sent'
            response_data['email_status'] = 'sent'
        else:
            response_message = 'User created successfully but email failed to send'
            response_data['email_status'] = 'failed'
            response_data['email_error'] = email_message
        
        return jsonify({
            'success': True,
            'message': response_message,
            'data': response_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.json
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({
            'success': False,
            'message': 'Email and password are required'
        }), 400
    
    try:
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Generate JWT token
        jwt_secret = os.getenv('JWT_TOKEN')
        if not jwt_secret:
            return jsonify({
                'success': False,
                'message': 'Server configuration error'
            }), 500
            
        token = jwt.encode({
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value,
            'exp': datetime.utcnow() + timedelta(days=7)
        }, jwt_secret, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': user.to_dict(),
                'token': token
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500