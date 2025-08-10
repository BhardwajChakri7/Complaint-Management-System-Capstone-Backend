from flask import Blueprint, request, jsonify
from utils.gemini_chatbot import gemini_chatbot
import jwt
import os
from functools import wraps
from datetime import datetime

# Create blueprint
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')

def token_optional(f):
    """Decorator for optional JWT token (allows both authenticated and anonymous users)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        current_user_id = None
        current_user_role = None
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            try:
                data = jwt.decode(token, os.getenv('JWT_TOKEN'), algorithms=['HS256'])
                current_user_id = data.get('user_id') or data.get('admin_id')
                current_user_role = data.get('role')
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                # Token is invalid, but we allow anonymous access
                pass
        
        return f(current_user_id, current_user_role, *args, **kwargs)
    
    return decorated

@chatbot_bp.route('/chat', methods=['POST'])
@token_optional
def chat_with_bot(current_user_id, current_user_role):
    """Main chatbot endpoint - handles user messages and returns AI responses"""
    try:
        data = request.get_json()
        
        if not data or not data.get('message'):
            return jsonify({
                'success': False,
                'message': 'Message is required'
            }), 400
        
        user_message = data['message'].strip()
        
        if len(user_message) < 1:
            return jsonify({
                'success': False,
                'message': 'Message cannot be empty'
            }), 400
        
        # Process the message with the chatbot
        response = gemini_chatbot.process_user_message(user_message, current_user_id)
        
        # Add user context to response
        response_data = {
            'user_message': user_message,
            'bot_response': response['message'],
            'success': response['success'],
            'timestamp': datetime.now().isoformat(),
            'user_authenticated': current_user_id is not None,
            'user_role': current_user_role
        }
        
        # Add additional data if available
        if response.get('ticket_id'):
            response_data['ticket_id'] = response['ticket_id']
        
        if response.get('complaint_data'):
            response_data['complaint_data'] = response['complaint_data']
        
        if response.get('has_complaint_data'):
            response_data['has_complaint_data'] = response['has_complaint_data']
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500

@chatbot_bp.route('/help', methods=['GET'])
def get_help():
    """Get chatbot help information"""
    try:
        help_message = gemini_chatbot.get_help_message()
        
        return jsonify({
            'success': True,
            'message': help_message,
            'available_commands': [
                'Check complaint status by ticket ID',
                'Ask general questions about complaints',
                'Get help with submitting complaints',
                'Learn about complaint categories'
            ],
            'example_queries': [
                "What's the status of CMP20241201ABCD?",
                "Check ticket CMP20241201ABCD",
                "How do I submit a complaint?",
                "What are the complaint categories?",
                "My complaint ID is CMP20241201ABCD"
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500

@chatbot_bp.route('/status', methods=['GET'])
def chatbot_status():
    """Get chatbot service status"""
    try:
        return jsonify({
            'success': True,
            'message': 'Chatbot service is running',
            'service': 'Gemini AI Chatbot',
            'version': '1.0',
            'features': [
                'Complaint status lookup by ticket ID',
                'AI-powered responses using Gemini 2.0 Flash',
                'Context-aware conversations',
                'User authentication support',
                'Multi-format ticket ID recognition'
            ],
            'supported_ticket_formats': [
                'CMP20241201ABCD',
                'CMP-20241201-ABCD', 
                'ticket: CMP20241201ABCD',
                'ID: CMP20241201ABCD',
                '#CMP20241201ABCD'
            ]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500

@chatbot_bp.route('/check-status', methods=['GET'])
@token_optional
def check_status(current_user_id, current_user_role):
    """Check complaint status by ticket ID"""
    try:
        ticket_id = request.args.get('ticket_id')
        
        if not ticket_id:
            return jsonify({
                'success': False,
                'message': 'Ticket ID is required'
            }), 400
        
        # Simulate a user message with the ticket ID
        user_message = f"What's the status of ticket {ticket_id}?"
        
        # Process with chatbot
        response = gemini_chatbot.process_user_message(user_message, current_user_id)
        
        return jsonify({
            'success': response['success'],
            'ticket_id': ticket_id,
            'message': response['message'],
            'has_complaint_data': response.get('has_complaint_data', False),
            'complaint_data': response.get('complaint_data'),
            'user_authenticated': current_user_id is not None,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500

@chatbot_bp.route('/quick-status/<ticket_id>', methods=['GET'])
@token_optional
def quick_status_check(current_user_id, current_user_role, ticket_id):
    """Quick status check endpoint for direct ticket ID lookup"""
    try:
        # Simulate a user message with the ticket ID
        user_message = f"What's the status of ticket {ticket_id}?"
        
        # Process with chatbot
        response = gemini_chatbot.process_user_message(user_message, current_user_id)
        
        return jsonify({
            'success': response['success'],
            'ticket_id': ticket_id,
            'message': response['message'],
            'has_complaint_data': response.get('has_complaint_data', False),
            'complaint_data': response.get('complaint_data'),
            'user_authenticated': current_user_id is not None,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500