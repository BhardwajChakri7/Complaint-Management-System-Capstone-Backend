from flask import Blueprint, request, jsonify
from models.admin import Admin
from models.user import db
from marshmallow import Schema, fields, ValidationError, validate
from utils.email_service import EmailService
import jwt
import os
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

class AdminSignupSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    number = fields.Str(required=True, validate=validate.Length(min=10, max=15))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

signup_schema = AdminSignupSchema()

@admin_bp.route('/signup', methods=['POST'])
def admin_signup():
    """Admin signup endpoint - Only one admin allowed"""
    try:
        # Check if admin already exists
        existing_admin = Admin.query.first()
        if existing_admin:
            return jsonify({
                'success': False,
                'message': 'Admin already exists. Only one admin is allowed.'
            }), 409
        
        # Validate request data
        data = signup_schema.load(request.json)
    except ValidationError as err:
        return jsonify({
            'success': False,
            'message': 'Validation error',
            'errors': err.messages
        }), 400
    
    try:
        # Check if email or number already exists
        existing_email = Admin.query.filter_by(email=data['email']).first()
        existing_number = Admin.query.filter_by(number=data['number']).first()
        
        if existing_email:
            return jsonify({
                'success': False,
                'message': 'Admin with this email already exists'
            }), 409
            
        if existing_number:
            return jsonify({
                'success': False,
                'message': 'Admin with this number already exists'
            }), 409
        
        # Create new admin
        new_admin = Admin(
            name=data['name'],
            number=data['number'],
            email=data['email'],
            password=data['password']
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        # Generate JWT token
        token = jwt.encode({
            'admin_id': new_admin.id,
            'email': new_admin.email,
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(days=7)
        }, os.getenv('JWT_TOKEN'), algorithm='HS256')
        
        # Send welcome email
        email_service = EmailService()
        email_sent, email_message = email_service.send_welcome_email(
            recipient_email=new_admin.email,
            recipient_name=new_admin.name,
            user_type="admin"
        )
        
        response_data = {
            'admin': new_admin.to_dict(),
            'token': token
        }
        
        # Add email status to response
        if email_sent:
            response_message = 'Admin created successfully and welcome email sent'
            response_data['email_status'] = 'sent'
        else:
            response_message = 'Admin created successfully but email failed to send'
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

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    data = request.json
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({
            'success': False,
            'message': 'Email and password are required'
        }), 400
    
    try:
        admin = Admin.query.filter_by(email=data['email']).first()
        
        if not admin or not admin.check_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Generate JWT token
        token = jwt.encode({
            'admin_id': admin.id,
            'email': admin.email,
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(days=7)
        }, os.getenv('JWT_TOKEN'), algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'Admin login successful',
            'data': {
                'admin': admin.to_dict(),
                'token': token
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500

@admin_bp.route('/profile', methods=['GET'])
def admin_profile():
    """Get admin profile - requires authentication"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            'success': False,
            'message': 'Authorization token required'
        }), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, os.getenv('JWT_TOKEN'), algorithms=['HS256'])
        admin_id = payload.get('admin_id')
        
        if not admin_id:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({
                'success': False,
                'message': 'Admin not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Admin profile retrieved successfully',
            'data': {
                'admin': admin.to_dict()
            }
        }), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({
            'success': False,
            'message': 'Token has expired'
        }), 401
    except jwt.InvalidTokenError:
        return jsonify({
            'success': False,
            'message': 'Invalid token'
        }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500