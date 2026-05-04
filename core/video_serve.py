import os
import re
from django.http import StreamingHttpResponse, HttpResponse, Http404
from django.conf import settings
from wsgiref.util import FileWrapper

def serve_video_with_range(request, path):
    """
    Custom view to serve media files with HTTP Range header support.
    This fixes the issue where HTML5 video players cannot seek/rewind
    in development mode because Django's default static server ignores Range requests.
    """
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("Video not found.")

    file_size = os.path.getsize(file_path)
    range_header = request.META.get('HTTP_RANGE', '').strip()
    
    # If no Range header, serve the whole file normally
    if not range_header:
        response = StreamingHttpResponse(FileWrapper(open(file_path, 'rb')), content_type='video/mp4')
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
        return response

    range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
    if not range_match:
        return HttpResponse(status=416) # Range Not Satisfiable

    first_byte, last_byte = range_match.groups()
    first_byte = int(first_byte) if first_byte else 0
    last_byte = int(last_byte) if last_byte else file_size - 1
    
    if last_byte >= file_size:
        last_byte = file_size - 1

    length = last_byte - first_byte + 1

    def file_iterator(file_path, offset=0, bytes_to_read=None, chunk_size=8192):
        with open(file_path, 'rb') as f:
            f.seek(offset)
            remaining = bytes_to_read
            while remaining > 0:
                chunk = f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                yield chunk
                remaining -= len(chunk)

    response = StreamingHttpResponse(
        file_iterator(file_path, offset=first_byte, bytes_to_read=length),
        status=206,
        content_type='video/mp4'
    )
    
    response['Content-Length'] = str(length)
    response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
    response['Accept-Ranges'] = 'bytes'
    return response
