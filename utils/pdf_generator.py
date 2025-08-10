from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
import os
import requests
from PIL import Image as PILImage
import tempfile

class ComplaintPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for the PDF"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Normal style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        )
        
        # Status style
        self.status_style = ParagraphStyle(
            'StatusStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.white
        )
    
    def download_image_from_url(self, image_url):
        """Download image from Cloudinary URL and return temporary file path"""
        try:
            print(f"🔄 Downloading image from: {image_url}")
            
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, timeout=15, headers=headers)
            response.raise_for_status()
            
            print(f"✅ Successfully downloaded image, size: {len(response.content)} bytes")
            
            # Determine file extension from URL or content type
            content_type = response.headers.get('content-type', '').lower()
            if 'jpeg' in content_type or 'jpg' in content_type:
                suffix = '.jpg'
            elif 'png' in content_type:
                suffix = '.png'
            elif 'gif' in content_type:
                suffix = '.gif'
            elif 'webp' in content_type:
                suffix = '.webp'
            else:
                # Default to jpg if we can't determine
                suffix = '.jpg'
            
            # Create temporary file with appropriate extension
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(response.content)
            temp_file.close()
            
            print(f"💾 Saved image to temporary file: {temp_file.name}")
            return temp_file.name
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error downloading image from {image_url}: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ Error downloading image from {image_url}: {str(e)}")
            return None
    
    def resize_image_for_pdf(self, image_path, max_width=4*inch, max_height=3*inch):
        """Resize image to fit within PDF constraints"""
        try:
            with PILImage.open(image_path) as img:
                # Calculate aspect ratio
                aspect_ratio = img.width / img.height
                
                # Determine new dimensions
                if img.width > img.height:
                    new_width = min(max_width, img.width)
                    new_height = new_width / aspect_ratio
                else:
                    new_height = min(max_height, img.height)
                    new_width = new_height * aspect_ratio
                
                # Ensure dimensions don't exceed limits
                if new_width > max_width:
                    new_width = max_width
                    new_height = new_width / aspect_ratio
                if new_height > max_height:
                    new_height = max_height
                    new_width = new_height * aspect_ratio
                
                return new_width, new_height
        except Exception as e:
            print(f"Error resizing image {image_path}: {str(e)}")
            return 2*inch, 1.5*inch  # Default size
    
    def generate_complaint_pdf(self, complaint_data):
        """Generate PDF for complaint ticket with embedded images"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        temp_files = []  # Keep track of temporary files to clean up
        
        try:
            # Add title with enhanced styling
            title = Paragraph("COMPLAINT MANAGEMENT SYSTEM", self.title_style)
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # Add ticket header with status color
            status_color = self.get_status_color(complaint_data.get('status', 'pending'))
            ticket_header = Paragraph(
                f"<b>Complaint Ticket: {complaint_data['ticket_id']}</b>", 
                self.header_style
            )
            elements.append(ticket_header)
            elements.append(Spacer(1, 12))
            
            # Create enhanced complaint details table
            complaint_details = [
                ['Field', 'Details'],
                ['Ticket ID', complaint_data['ticket_id']],
                ['User Name', complaint_data['user_name']],
                ['User Email', complaint_data['user_email']],
                ['Title', complaint_data['title']],
                ['Category', complaint_data['category']],
                ['Priority', complaint_data['priority']],
                ['Status', complaint_data['status']],
                ['Created At', complaint_data['created_at']],
                ['Updated At', complaint_data['updated_at']]
            ]
            
            # Add resolved date if available
            if complaint_data.get('resolved_at'):
                complaint_details.append(['Resolved At', complaint_data['resolved_at']])
            
            # Add admin info if available
            if complaint_data.get('admin_id'):
                complaint_details.append(['Handled By Admin ID', str(complaint_data['admin_id'])])
            
            # Create table with enhanced styling
            table = Table(complaint_details, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 20))
            
            # Add description with better formatting
            desc_header = Paragraph("<b>Description:</b>", self.header_style)
            elements.append(desc_header)
            
            # Format description with proper line breaks
            formatted_description = complaint_data['description'].replace('\n', '<br/>')
            description = Paragraph(formatted_description, self.normal_style)
            elements.append(description)
            elements.append(Spacer(1, 20))
            
            # Add attachments with embedded images
            if complaint_data.get('attachments'):
                att_header = Paragraph("<b>Attachments:</b>", self.header_style)
                elements.append(att_header)
                elements.append(Spacer(1, 10))
                
                for i, attachment in enumerate(complaint_data['attachments']):
                    # Add attachment info with proper file size formatting
                    file_size = attachment.get('file_size', 'Unknown size')
                    if isinstance(file_size, int):
                        # Convert bytes to human readable format
                        if file_size < 1024:
                            file_size_str = f"{file_size} bytes"
                        elif file_size < 1024 * 1024:
                            file_size_str = f"{file_size / 1024:.1f} KB"
                        else:
                            file_size_str = f"{file_size / (1024 * 1024):.1f} MB"
                    else:
                        file_size_str = str(file_size)
                    
                    att_info = Paragraph(
                        f"<b>{i+1}. {attachment['original_filename']}</b> ({attachment['file_type']}) - {file_size_str}", 
                        self.normal_style
                    )
                    elements.append(att_info)
                    elements.append(Spacer(1, 5))
                    
                    # Check if it's an image file
                    file_type = attachment.get('file_type', '').lower()
                    original_filename = attachment.get('original_filename', '').lower()
                    image_url = attachment.get('file_url', '')
                    
                    print(f"Processing attachment: {attachment.get('original_filename')}")
                    print(f"File type: {file_type}")
                    print(f"Image URL: {image_url}")
                    
                    # Check if it's an image by file type or file extension
                    is_image = (
                        file_type in ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'] or
                        any(original_filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
                    )
                    
                    if is_image and image_url:
                        print(f"Attempting to download and embed image: {image_url}")
                        temp_image_path = self.download_image_from_url(image_url)
                        if temp_image_path:
                            temp_files.append(temp_image_path)
                            try:
                                print(f"Successfully downloaded image to: {temp_image_path}")
                                
                                # Get appropriate dimensions
                                width, height = self.resize_image_for_pdf(temp_image_path)
                                print(f"Image dimensions: {width} x {height}")
                                
                                # Create image object and add to PDF
                                img = Image(temp_image_path, width=width, height=height)
                                elements.append(img)
                                elements.append(Spacer(1, 10))
                                
                                # Add image caption
                                caption = Paragraph(
                                    f"<i>Image: {attachment['original_filename']}</i>", 
                                    ParagraphStyle('Caption', parent=self.styles['Normal'],
                                                 fontSize=9, alignment=TA_CENTER,
                                                 textColor=colors.grey)
                                )
                                elements.append(caption)
                                elements.append(Spacer(1, 15))
                                
                                print(f"✅ Successfully embedded image: {attachment['original_filename']}")
                                
                            except Exception as e:
                                print(f"❌ Error adding image to PDF: {str(e)}")
                                # Add error message instead of image
                                error_msg = Paragraph(
                                    f"<i>Could not display image: {attachment['original_filename']} - Error: {str(e)}</i>", 
                                    ParagraphStyle('Error', parent=self.styles['Normal'],
                                                 fontSize=9, textColor=colors.red)
                                )
                                elements.append(error_msg)
                                elements.append(Spacer(1, 10))
                        else:
                            print(f"❌ Failed to download image from: {image_url}")
                            # Add download failure message
                            error_msg = Paragraph(
                                f"<i>Could not download image: {attachment['original_filename']}</i>", 
                                ParagraphStyle('Error', parent=self.styles['Normal'],
                                             fontSize=9, textColor=colors.red)
                            )
                            elements.append(error_msg)
                            elements.append(Spacer(1, 10))
                    else:
                        # For non-image files, just show the URL
                        print(f"Non-image file, showing URL: {attachment.get('original_filename')}")
                        if image_url:
                            file_link = Paragraph(
                                f"<i>File URL: <a href='{image_url}'>{attachment['original_filename']}</a></i>", 
                                ParagraphStyle('FileLink', parent=self.styles['Normal'],
                                             fontSize=9, textColor=colors.blue)
                            )
                            elements.append(file_link)
                            elements.append(Spacer(1, 10))
                
                elements.append(Spacer(1, 10))
            
            # Add admin response if available
            if complaint_data.get('admin_response'):
                response_header = Paragraph("<b>Admin Response:</b>", self.header_style)
                elements.append(response_header)
                
                # Format admin response with proper line breaks
                formatted_response = complaint_data['admin_response'].replace('\n', '<br/>')
                response = Paragraph(formatted_response, self.normal_style)
                elements.append(response)
                elements.append(Spacer(1, 20))
            
            # Add status timeline if available
            if complaint_data.get('status_history'):
                timeline_header = Paragraph("<b>Status Timeline:</b>", self.header_style)
                elements.append(timeline_header)
                
                for status_entry in complaint_data['status_history']:
                    timeline_entry = Paragraph(
                        f"• {status_entry['date']}: {status_entry['status']} - {status_entry.get('note', 'No additional notes')}", 
                        self.normal_style
                    )
                    elements.append(timeline_entry)
                elements.append(Spacer(1, 20))
            
            # Add footer with enhanced information
            footer_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Complaint Management System v1.0"
            footer = Paragraph(footer_text, ParagraphStyle('Footer', parent=self.styles['Normal'],
                                                         fontSize=8, alignment=TA_CENTER,
                                                         textColor=colors.grey))
            elements.append(Spacer(1, 30))
            elements.append(footer)
            
            # Build PDF
            doc.build(elements)
            
            # Get the value of the BytesIO buffer
            pdf_data = buffer.getvalue()
            buffer.close()
            
            return pdf_data
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            buffer.close()
            raise e
        
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    print(f"Error cleaning up temp file {temp_file}: {str(e)}")
    
    def get_status_color(self, status):
        """Get color based on status"""
        status_colors = {
            'pending': colors.orange,
            'in_progress': colors.blue,
            'resolved': colors.green,
            'closed': colors.grey
        }
        return status_colors.get(status.lower(), colors.black)
    
    def get_priority_color(self, priority):
        """Get color based on priority"""
        priority_colors = {
            'low': colors.green,
            'medium': colors.orange,
            'high': colors.red,
            'urgent': colors.darkred
        }
        return priority_colors.get(priority.lower(), colors.black)