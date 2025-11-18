from django.http import HttpResponse, Http404
from django.conf import settings
import os
import mimetypes

def serve_media(request, path):
    """Custom media serving view for development"""
    if not settings.DEBUG:
        raise Http404("Media serving is only available in debug mode")
    
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    if not os.path.exists(file_path):
        raise Http404("File not found")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'
    
    # Read and return the file
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=content_type)
        return response
