#!/usr/bin/env python3
"""
Gemini AI Chatbot Service for Complaint Management System
Handles user queries and fetches complaint status by ticket ID
"""

import requests
import json
import re
import os
from datetime import datetime
from models.complaint import Complaint, ComplaintStatus, ComplaintCategory, ComplaintPriority
from models.user import User
from models.admin import Admin

class GeminiChatbot:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API', 'AIzaSyC5zkT6SXMVOxsNMZF9b7HrAgd4b8d6C_0')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.api_key
        }
    
    def extract_ticket_id(self, user_message):
        """Extract ticket ID from user message using regex patterns"""
        # Common patterns for ticket IDs
        patterns = [
            r'CMP\d{8}[A-Z0-9]{4}',  # CMP20241201ABCD format
            r'CMP-\d{8}-[A-Z0-9]{4}',  # CMP-20241201-ABCD format
            r'CMP[A-Z0-9]{12}',  # CMPABCD12345678 format
            r'ticket[:\s]+([A-Z0-9-]+)',  # "ticket: ABC123" or "ticket ABC123"
            r'ID[:\s]+([A-Z0-9-]+)',  # "ID: ABC123" or "ID ABC123"
            r'#([A-Z0-9-]+)',  # "#ABC123"
        ]
        
        user_message_upper = user_message.upper()
        
        for pattern in patterns:
            matches = re.findall(pattern, user_message_upper)
            if matches:
                return matches[0] if isinstance(matches[0], str) else matches[0]
        
        return None
    
    def get_complaint_by_ticket_id(self, ticket_id):
        """Fetch complaint details from database by ticket ID"""
        try:
            complaint = Complaint.query.filter_by(ticket_id=ticket_id).first()
            if complaint:
                return complaint.to_dict()
            return None
        except Exception as e:
            print(f"Error fetching complaint {ticket_id}: {str(e)}")
            return None
    
    def format_complaint_status(self, complaint_data):
        """Format complaint data into a readable status message"""
        if not complaint_data:
            return "❌ Complaint not found. Please check your ticket ID and try again."
        
        status_emoji = {
            'pending': '🟡',
            'in_progress': '🔵', 
            'resolved': '🟢',
            'closed': '⚫'
        }
        
        priority_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'urgent': '🔴'
        }
        
        category_emoji = {
            'Technical': '💻',
            'Academic': '📚',
            'Hostel/Mess': '🏠',
            'Maintenance': '🔧'
        }
        
        status_msg = f"""
📋 **Complaint Status Report**

🎫 **Ticket ID:** {complaint_data['ticket_id']}
👤 **User:** {complaint_data['user_name']} ({complaint_data['user_email']})
📝 **Title:** {complaint_data['title']}

{category_emoji.get(complaint_data['category'], '📂')} **Category:** {complaint_data['category']}
{priority_emoji.get(complaint_data['priority'], '⚪')} **Priority:** {complaint_data['priority'].title()}
{status_emoji.get(complaint_data['status'], '⚪')} **Status:** {complaint_data['status'].replace('_', ' ').title()}

📅 **Created:** {complaint_data['created_at'][:19].replace('T', ' ')}
🔄 **Updated:** {complaint_data['updated_at'][:19].replace('T', ' ')}
"""
        
        if complaint_data.get('resolved_at'):
            status_msg += f"✅ **Resolved:** {complaint_data['resolved_at'][:19].replace('T', ' ')}\n"
        
        if complaint_data.get('admin_response'):
            status_msg += f"\n💬 **Admin Response:**\n{complaint_data['admin_response']}\n"
        
        if complaint_data.get('attachments'):
            status_msg += f"\n📎 **Attachments:** {len(complaint_data['attachments'])} file(s)\n"
        
        # Add next steps based on status
        if complaint_data['status'] == 'pending':
            status_msg += "\n⏳ **Next Steps:** Your complaint is in queue and will be reviewed by our admin team within 24-48 hours."
        elif complaint_data['status'] == 'in_progress':
            status_msg += "\n🔄 **Next Steps:** Your complaint is being actively worked on. You'll receive updates as progress is made."
        elif complaint_data['status'] == 'resolved':
            status_msg += "\n✅ **Next Steps:** Your complaint has been resolved. If you're satisfied, no further action is needed."
        elif complaint_data['status'] == 'closed':
            status_msg += "\n⚫ **Next Steps:** This complaint has been closed. Contact support if you need to reopen it."
        
        return status_msg
    
    def generate_ai_response(self, user_message, complaint_data=None):
        """Generate AI response using Gemini API"""
        try:
            # Create context-aware prompt
            if complaint_data:
                system_context = f"""
You are a helpful customer service chatbot for a Complaint Management System. 
The user is asking about their complaint with the following details:
- Ticket ID: {complaint_data['ticket_id']}
- Status: {complaint_data['status']}
- Category: {complaint_data['category']}
- Priority: {complaint_data['priority']}
- Title: {complaint_data['title']}

Provide a helpful, empathetic response about their complaint status. Be professional and reassuring.
"""
            else:
                system_context = """
You are a helpful customer service chatbot for a Complaint Management System.
Help users with their queries about complaints, ticket status, and general support.
If they mention a ticket ID, acknowledge it and provide relevant information.
Be professional, empathetic, and helpful.
"""
            
            prompt = f"{system_context}\n\nUser message: {user_message}\n\nResponse:"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
                return ai_response.strip()
            else:
                return "I apologize, but I'm having trouble generating a response right now. Please try again later."
                
        except requests.exceptions.RequestException as e:
            print(f"Error calling Gemini API: {str(e)}")
            return "I'm currently experiencing technical difficulties. Please try again in a moment."
        except Exception as e:
            print(f"Error generating AI response: {str(e)}")
            return "I apologize for the inconvenience. Please contact our support team for assistance."
    
    def process_user_message(self, user_message, user_id=None):
        """Main method to process user messages and return appropriate responses"""
        try:
            # Extract ticket ID if present
            ticket_id = self.extract_ticket_id(user_message)
            complaint_data = None
            
            if ticket_id:
                complaint_data = self.get_complaint_by_ticket_id(ticket_id)
                
                if complaint_data:
                    # Check if user has access to this complaint (if user_id provided)
                    if user_id and complaint_data['user_id'] != user_id:
                        return {
                            'success': False,
                            'message': "🔒 Access denied. You can only view your own complaints.",
                            'ticket_id': ticket_id,
                            'has_complaint_data': False
                        }
                    
                    # Return formatted status + AI response
                    status_info = self.format_complaint_status(complaint_data)
                    ai_response = self.generate_ai_response(user_message, complaint_data)
                    
                    return {
                        'success': True,
                        'message': f"{status_info}\n\n🤖 **AI Assistant:**\n{ai_response}",
                        'ticket_id': ticket_id,
                        'complaint_data': complaint_data,
                        'has_complaint_data': True
                    }
                else:
                    # Ticket ID found but complaint doesn't exist
                    ai_response = self.generate_ai_response(f"User is asking about ticket {ticket_id} but it doesn't exist in our system.")
                    return {
                        'success': False,
                        'message': f"❌ Ticket ID '{ticket_id}' not found in our system.\n\n🤖 **AI Assistant:**\n{ai_response}",
                        'ticket_id': ticket_id,
                        'has_complaint_data': False
                    }
            else:
                # No ticket ID found, general AI response
                ai_response = self.generate_ai_response(user_message)
                return {
                    'success': True,
                    'message': f"🤖 **AI Assistant:**\n{ai_response}",
                    'ticket_id': None,
                    'has_complaint_data': False
                }
                
        except Exception as e:
            print(f"Error processing user message: {str(e)}")
            return {
                'success': False,
                'message': "I apologize, but I'm experiencing technical difficulties. Please try again later or contact our support team.",
                'error': str(e)
            }
    
    def get_help_message(self):
        """Return help message for users"""
        return """
🤖 **AI Chatbot Help**

I can help you with:
✅ Check complaint status by ticket ID
✅ General questions about the complaint system
✅ Guidance on submitting complaints
✅ Information about complaint categories and priorities

**How to check your complaint status:**
- Just mention your ticket ID (e.g., "CMP20241201ABCD")
- Or ask: "What's the status of ticket CMP20241201ABCD?"
- Or: "Check my complaint #CMP20241201ABCD"

**Example queries:**
- "What's the status of CMP20241201ABCD?"
- "Check ticket CMP20241201ABCD"
- "My complaint ID is CMP20241201ABCD, what's the update?"
- "How do I submit a complaint?"
- "What are the different complaint categories?"

Feel free to ask me anything! 😊
"""

# Global chatbot instance
gemini_chatbot = GeminiChatbot()