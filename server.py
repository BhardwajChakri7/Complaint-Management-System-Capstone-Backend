from flask import Flask, jsonify
from flask_cors import CORS
from flask_mail import Mail
from models.user import db
from models.admin import Admin
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.complaints import complaints_bp
from routes.chatbot import chatbot_bp
from trained_models.standalone_ml import ml_bp
from utils.email_service import email_service
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('NEON_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=["https://queriespro.vercel.app", "http://127.0.0.1:5173","http://localhost:5173"], supports_credentials=True, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Initialize email service
    email_service.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(ml_bp)
    
    # Health check endpoint
    @app.route('/', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Server is running',
            'port': 6969
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
    
    return app
app = create_app()
if __name__ == '__main__':
    app = create_app()
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    print("Starting server on port 6969...")
    app.run(host='0.0.0.0', port=6969, debug=True)