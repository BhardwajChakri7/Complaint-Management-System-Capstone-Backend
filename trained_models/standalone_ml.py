#!/usr/bin/env python3
"""
Standalone ML service that works without any external ML dependencies
This is a guaranteed fallback that will always work
"""

import os
import re
from flask import Blueprint, request, jsonify
import jwt
from functools import wraps

# Create blueprint
ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')

class StandaloneMLService:
    def __init__(self):
        self.models_loaded = False
        self.training_data = []
        self.category_patterns = {}
        self.priority_patterns = {}
        self.load_csv_data()
        self.build_patterns()
    
    def load_csv_data(self):
        """Load training data from CSV file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, "cmsdata.csv")
            
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    # Skip header
                    for line in lines[1:]:
                        parts = line.strip().split(',', 2)
                        if len(parts) >= 3:
                            query = parts[0].strip('"')
                            category = parts[1].strip('"')
                            priority = parts[2].strip('"')
                            self.training_data.append({
                                'query': query,
                                'category': category,
                                'priority': priority
                            })
                
                self.models_loaded = True
            else:
                print("⚠️ CSV file not found - using default patterns")
                self.setup_default_patterns()
                
        except Exception as e:
            print(f"⚠️ Error loading CSV: {e} - using default patterns")
            self.setup_default_patterns()
    
    def build_patterns(self):
        """Build classification patterns from training data"""
        if not self.training_data:
            self.setup_default_patterns()
            return
        
        # Build word frequency patterns
        category_words = {}
        priority_words = {}
        
        for item in self.training_data:
            words = self.extract_words(item['query'])
            category = item['category']
            priority = item['priority']
            
            if category not in category_words:
                category_words[category] = {}
            if priority not in priority_words:
                priority_words[priority] = {}
            
            for word in words:
                category_words[category][word] = category_words[category].get(word, 0) + 1
                priority_words[priority][word] = priority_words[priority].get(word, 0) + 1
        
        # Extract top words for each category/priority
        self.category_patterns = {}
        for category, words in category_words.items():
            # Get top 50 words for this category
            sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)[:50]
            self.category_patterns[category] = [word for word, count in sorted_words if count > 1]
        
        self.priority_patterns = {}
        for priority, words in priority_words.items():
            # Get top 30 words for this priority
            sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)[:30]
            self.priority_patterns[priority] = [word for word, count in sorted_words if count > 1]
        
        if self.models_loaded:
            print("✅ ML models loaded successfully")
    
    def setup_default_patterns(self):
        """Setup default patterns if CSV is not available"""
        self.category_patterns = {
            'Technical': ['login', 'password', 'portal', 'wifi', 'internet', 'network', 'computer', 'laptop', 'software', 'email', 'lms', 'system'],
            'Academic': ['grade', 'marks', 'exam', 'attendance', 'lecture', 'class', 'assignment', 'certificate', 'transfer', 'timetable', 'professor'],
            'Hostel/Mess': ['hostel', 'room', 'mess', 'food', 'meal', 'accommodation', 'furniture', 'allotment', 'quality', 'dining'],
            'Maintenance': ['maintenance', 'repair', 'broken', 'electricity', 'water', 'tap', 'elevator', 'cleaning', 'lighting', 'conditioning']
        }
        
        self.priority_patterns = {
            'urgent': ['urgent', 'emergency', 'immediately', 'broken', 'not', 'working', 'critical'],
            'high': ['important', 'soon', 'needed', 'missing', 'exam', 'grade', 'deteriorated'],
            'medium': ['moderate', 'normal', 'permission', 'competition', 'week'],
            'low': ['later', 'minor', 'simple', 'routine', 'cleaning', 'dim']
        }
    
    def extract_words(self, text):
        """Extract meaningful words from text"""
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        words = [word for word in text.split() if len(word) > 2]
        return words
    
    def classify_user_query(self, query):
        """Advanced classification using multiple techniques"""
        words = self.extract_words(query)
        query_lower = query.lower()
        
        # 1. Rule-based classification for specific cases
        category, priority = self.rule_based_classification(query_lower, words)
        if category:
            return category, priority
        
        # 2. Pattern-based classification with weighted scoring
        category_scores = {}
        for category, patterns in self.category_patterns.items():
            score = 0
            for word in words:
                if word in patterns:
                    # Give higher weight to exact matches
                    score += 2
                # Check for partial matches
                for pattern in patterns:
                    if pattern in word or word in pattern:
                        score += 0.5
            category_scores[category] = score
        
        # 3. Context-aware classification
        category_scores = self.apply_context_rules(query_lower, words, category_scores)
        
        predicted_category = max(category_scores, key=category_scores.get) if category_scores else 'Technical'
        
        # Priority classification with context
        priority_scores = {}
        for priority, patterns in self.priority_patterns.items():
            score = sum(2 if word in patterns else 0 for word in words)
            priority_scores[priority] = score
        
        # Apply priority context rules
        priority_scores = self.apply_priority_context(query_lower, words, predicted_category, priority_scores)
        
        predicted_priority = max(priority_scores, key=priority_scores.get) if max(priority_scores.values()) > 0 else 'medium'
        
        return predicted_category, predicted_priority
    
    def rule_based_classification(self, query_lower, words):
        """Rule-based classification for specific patterns"""
        
        # Water-related issues
        if any(word in query_lower for word in ['water', 'tap', 'leak', 'plumbing', 'pipe', 'drainage']):
            if any(word in query_lower for word in ['hostel', 'room', 'mess']):
                return 'Hostel/Mess', 'urgent'
            else:
                return 'Maintenance', 'urgent'
        
        # Electrical issues
        if any(word in query_lower for word in ['electricity', 'power', 'light', 'bulb', 'electrical']):
            if any(word in query_lower for word in ['hostel', 'room']):
                return 'Hostel/Mess', 'urgent'
            else:
                return 'Maintenance', 'high'
        
        # Food/Mess issues
        if any(word in query_lower for word in ['food', 'meal', 'mess', 'dining', 'kitchen', 'quality']):
            return 'Hostel/Mess', 'high'
        
        # Room/Accommodation issues
        if any(word in query_lower for word in ['room', 'furniture', 'bed', 'chair', 'table']):
            return 'Hostel/Mess', 'medium'
        
        # Login/Portal issues
        if any(word in query_lower for word in ['login', 'portal', 'password', 'access']):
            return 'Technical', 'urgent'
        
        # Wi-Fi/Network issues
        if any(word in query_lower for word in ['wifi', 'internet', 'network', 'connection']):
            return 'Technical', 'urgent'
        
        # Academic issues
        if any(word in query_lower for word in ['grade', 'marks', 'exam', 'certificate', 'attendance']):
            return 'Academic', 'high'
        
        # Maintenance issues
        if any(word in query_lower for word in ['broken', 'repair', 'fix', 'maintenance', 'elevator', 'lift']):
            return 'Maintenance', 'urgent'
        
        return None, None
    
    def apply_context_rules(self, query_lower, words, category_scores):
        """Apply context-aware rules to improve category classification"""
        
        # Boost scores based on context
        if 'hostel' in query_lower or 'room' in query_lower:
            category_scores['Hostel/Mess'] = category_scores.get('Hostel/Mess', 0) + 3
            
        if any(word in query_lower for word in ['broken', 'not working', 'repair', 'fix']):
            category_scores['Maintenance'] = category_scores.get('Maintenance', 0) + 2
            
        if any(word in query_lower for word in ['portal', 'system', 'software', 'computer']):
            category_scores['Technical'] = category_scores.get('Technical', 0) + 2
            
        if any(word in query_lower for word in ['exam', 'grade', 'class', 'lecture']):
            category_scores['Academic'] = category_scores.get('Academic', 0) + 2
        
        return category_scores
    
    def apply_priority_context(self, query_lower, words, category, priority_scores):
        """Apply context rules for priority classification"""
        
        # Urgent indicators
        if any(word in query_lower for word in ['urgent', 'emergency', 'immediately', 'asap']):
            priority_scores['urgent'] = priority_scores.get('urgent', 0) + 5
            
        if any(word in query_lower for word in ['broken', 'not working', 'damaged']):
            priority_scores['urgent'] = priority_scores.get('urgent', 0) + 3
            
        # High priority indicators
        if any(word in query_lower for word in ['important', 'needed', 'required', 'missing']):
            priority_scores['high'] = priority_scores.get('high', 0) + 2
            
        if any(word in query_lower for word in ['exam', 'grade', 'certificate']):
            priority_scores['high'] = priority_scores.get('high', 0) + 2
            
        # Category-based priority adjustment
        if category == 'Maintenance' and any(word in query_lower for word in ['water', 'electricity', 'elevator']):
            priority_scores['urgent'] = priority_scores.get('urgent', 0) + 2
            
        if category == 'Technical' and any(word in query_lower for word in ['login', 'portal', 'wifi']):
            priority_scores['urgent'] = priority_scores.get('urgent', 0) + 2
        
        return priority_scores

# Initialize the standalone service
ml_service = StandaloneMLService()

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Token is missing'
            }), 401
        
        try:
            data = jwt.decode(token, os.getenv('JWT_TOKEN'), algorithms=['HS256'])
            current_user_id = data.get('user_id') or data.get('admin_id')
            current_user_role = data.get('role')
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Token is invalid'
            }), 401
        
        return f(current_user_id, current_user_role, *args, **kwargs)
    
    return decorated

@ml_bp.route('/classify', methods=['POST'])
@token_required
def classify_query(current_user_id, current_user_role):
    """Classify user query endpoint - requires authentication"""
    try:
        data = request.json
        
        if not data or not data.get('query'):
            return jsonify({
                'success': False,
                'message': 'Query text is required'
            }), 400
        
        query_text = data['query'].strip()
        
        if len(query_text) < 5:
            return jsonify({
                'success': False,
                'message': 'Query text must be at least 5 characters long'
            }), 400
        
        # Classify the query
        category, priority = ml_service.classify_user_query(query_text)
        
        return jsonify({
            'success': True,
            'message': 'Query classified successfully',
            'data': {
                'query': query_text,
                'predicted_category': category,
                'predicted_priority': priority,
                'user_id': current_user_id,
                'user_role': current_user_role,
                'models_loaded': ml_service.models_loaded,
                'classification_method': 'CSV-based Pattern Matching'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': str(e)
        }), 500

@ml_bp.route('/status', methods=['GET'])
@token_required
def ml_status(current_user_id, current_user_role):
    """Get ML model status - requires authentication"""
    return jsonify({
        'success': True,
        'message': 'ML service status',
        'data': {
            'models_loaded': ml_service.models_loaded,
            'available_categories': list(ml_service.category_patterns.keys()),
            'available_priorities': list(ml_service.priority_patterns.keys()),
            'classification_method': 'CSV-based Pattern Matching',
            'training_samples': len(ml_service.training_data),
            'available_endpoints': ['/api/ml/classify', '/api/ml/status'],
            'user_id': current_user_id,
            'user_role': current_user_role
        }
    }), 200