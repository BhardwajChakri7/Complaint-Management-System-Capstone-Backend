import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

class CloudinaryService:
    def __init__(self):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.getenv('CLOUD_NAME'),
            api_key=os.getenv('CLOUD_API_KEY'),
            api_secret=os.getenv('CLOUD_API_SECRET')
        )
        
        # Allowed file extensions
        self.allowed_extensions = {
            'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'},
            'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
            'spreadsheets': {'xls', 'xlsx', 'csv'},
            'presentations': {'ppt', 'pptx'},
            'archives': {'zip', 'rar', '7z'},
            'audio': {'mp3', 'wav', 'ogg', 'm4a'},
            'video': {'mp4', 'avi', 'mov', 'wmv', 'flv'}
        }
        
        # Max file size (10MB)
        self.max_file_size = 10 * 1024 * 1024
    
    def is_allowed_file(self, filename):
        """Check if file extension is allowed"""
        if not filename or '.' not in filename:
            return False, "No file extension found"
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return True, file_type
        
        return False, "File type not allowed"
    
    def get_file_type(self, filename):
        """Get file type category"""
        if not filename or '.' not in filename:
            return "unknown"
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return file_type
        
        return "unknown"
    
    def upload_file(self, file, folder="complaints"):
        """Upload file to Cloudinary"""
        try:
            # Check if file is allowed
            is_allowed, file_type_or_error = self.is_allowed_file(file.filename)
            if not is_allowed:
                return {
                    'success': False,
                    'error': file_type_or_error
                }
            
            # Check file size
            file.seek(0, 2)  # Seek to end of file
            file_size = file.tell()
            file.seek(0)  # Reset file pointer
            
            if file_size > self.max_file_size:
                return {
                    'success': False,
                    'error': f"File size exceeds maximum limit of {self.max_file_size // (1024*1024)}MB"
                }
            
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename_without_ext = os.path.splitext(original_filename)[0]
            extension = os.path.splitext(original_filename)[1]
            
            unique_filename = f"{filename_without_ext}_{timestamp}_{unique_id}{extension}"
            public_id = f"{folder}/{unique_filename}"
            
            # Upload to Cloudinary
            if file_type_or_error == 'images':
                # For images, use image upload
                upload_result = cloudinary.uploader.upload(
                    file,
                    public_id=public_id,
                    folder=folder,
                    resource_type="image",
                    quality="auto",
                    fetch_format="auto"
                )
            else:
                # For other files, use raw upload
                upload_result = cloudinary.uploader.upload(
                    file,
                    public_id=public_id,
                    folder=folder,
                    resource_type="raw"
                )
            
            return {
                'success': True,
                'data': {
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'file_url': upload_result['secure_url'],
                    'file_type': file_type_or_error,
                    'file_size': file_size,
                    'cloudinary_public_id': upload_result['public_id']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Upload failed: {str(e)}"
            }
    
    def upload_multiple_files(self, files, folder="complaints"):
        """Upload multiple files to Cloudinary"""
        results = []
        
        for file in files:
            if file and file.filename:
                result = self.upload_file(file, folder)
                results.append({
                    'filename': file.filename,
                    'result': result
                })
        
        return results
    
    def delete_file(self, public_id, resource_type="auto"):
        """Delete file from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            return {
                'success': result.get('result') == 'ok',
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_info(self, public_id, resource_type="auto"):
        """Get file information from Cloudinary"""
        try:
            result = cloudinary.api.resource(public_id, resource_type=resource_type)
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_signed_url(self, public_id, resource_type="auto", expires_in=3600):
        """Generate signed URL for secure file access"""
        try:
            url = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type=resource_type,
                sign_url=True,
                expires_at=expires_in
            )[0]
            
            return {
                'success': True,
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global cloudinary service instance
cloudinary_service = CloudinaryService()