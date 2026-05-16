"""
Performance optimization middleware for Django
Adds caching headers, compression support, and performance improvements
"""

from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.cache import add_never_cache_headers
import gzip
from io import BytesIO
import logging


logger = logging.getLogger(__name__)


class PerformanceOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware to optimize performance by:
    - Adding proper cache headers
    - Enabling compression
    - Removing unnecessary headers
    """
    
    def process_response(self, request, response):
        try:
            # Add cache headers for static resources
            if self._is_static_resource(request.path):
                response['Cache-Control'] = 'public, max-age=31536000, immutable'
                response['Expires'] = self._get_expires_header()

            # Add cache headers for HTML pages (shorter duration)
            elif response.get('Content-Type', '').startswith('text/html'):
                response['Cache-Control'] = 'public, max-age=300'

            # Remove server version header for security
            if 'Server' in response:
                del response['Server']

            # Do not compress streaming responses in custom middleware.
            if not getattr(response, 'streaming', False) and self._should_compress(response):
                response = self._compress_response(response)
        except Exception:
            logger.exception('Performance middleware failed; returning original response')

        return response
    
    @staticmethod
    def _is_static_resource(path):
        """Check if the request is for a static resource"""
        static_extensions = (
            '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp',
            '.woff', '.woff2', '.ttf', '.eot', '.ico'
        )
        return any(path.endswith(ext) for ext in static_extensions)
    
    @staticmethod
    def _should_compress(response):
        """Check if response should be compressed"""
        if getattr(response, 'streaming', False):
            return False

        content_type = response.get('Content-Type', '')
        compressible_types = (
            'text/html', 'text/css', 'application/javascript',
            'application/json', 'text/plain', 'text/xml'
        )
        
        # Skip if already compressed or too small
        content_length = len(response.content)
        if content_length < 1024:  # Less than 1KB
            return False
        
        if response.get('Content-Encoding'):
            return False
        
        return any(content_type.startswith(ct) for ct in compressible_types)
    
    @staticmethod
    def _compress_response(response):
        """Compress response content using gzip"""
        if response.get('Content-Encoding'):
            return response
        
        content = response.content
        gzip_buffer = BytesIO()
        
        try:
            with gzip.GzipFile(
                mode='wb',
                fileobj=gzip_buffer,
                compresslevel=6,
                mtime=0
            ) as gz_file:
                gz_file.write(content)
            
            compressed_content = gzip_buffer.getvalue()
            
            # Only use compressed version if smaller
            if len(compressed_content) < len(content):
                response.content = compressed_content
                response['Content-Encoding'] = 'gzip'
                response['Content-Length'] = len(compressed_content)
        except Exception:
            # If compression fails, return original response
            pass
        
        return response
    
    @staticmethod
    def _get_expires_header():
        """Generate Expires header (1 year from now)"""
        from datetime import datetime, timedelta
        future = datetime.utcnow() + timedelta(days=365)
        return future.strftime('%a, %d %b %Y %H:%M:%S GMT')


class MobileOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware to detect and optimize for mobile devices
    """
    
    MOBILE_USER_AGENTS = [
        'Mobile',
        'Android',
        'iPhone',
        'iPad',
        'BlackBerry',
        'Opera Mini',
        'IEMobile',
        'Windows Phone'
    ]
    
    def process_request(self, request):
        """Detect if request is from a mobile device"""
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        is_mobile = any(ua in user_agent for ua in self.MOBILE_USER_AGENTS)
        request.is_mobile = is_mobile
        return None
    
    def process_response(self, request, response):
        """Add mobile optimization headers"""
        if hasattr(request, 'is_mobile') and request.is_mobile:
            # Add mobile-specific cache directives
            response['X-Mobile-Optimized'] = 'true'
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers for better protection
    """
    
    def process_response(self, request, response):
        # Clickjacking protection
        if 'X-Frame-Options' not in response:
            response['X-Frame-Options'] = 'SAMEORIGIN'
        
        # XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # MIME type sniffing protection
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature policy / Permissions policy
        response['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=()'
        )
        
        return response
