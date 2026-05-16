from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.utils._os import safe_join
from django.views.static import serve
from pathlib import Path


def serve_media_or_placeholder(request, path):
	full_path = Path(safe_join(settings.MEDIA_ROOT, path))
	if full_path.exists() and full_path.is_file():
		return serve(request, path, document_root=settings.MEDIA_ROOT)

	svg = """<svg xmlns="http://www.w3.org/2000/svg" width="420" height="280" viewBox="0 0 420 280">
		<rect width="420" height="280" fill="#f5f7f8"/>
		<rect x="24" y="24" width="372" height="232" rx="8" fill="#ffffff" stroke="#dce5e1"/>
		<text x="210" y="132" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#14532d">الصورة غير متوفرة</text>
		<text x="210" y="164" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#65716d">أعد رفع الصورة بعد تفعيل Cloudinary</text>
	</svg>"""
	return HttpResponse(svg, content_type='image/svg+xml', status=200)

urlpatterns=[
	path('admin/',admin.site.urls),
	path('',include('evaluations.urls')),
	re_path(r'^media/(?P<path>.*)$', serve_media_or_placeholder),
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
