from django.urls import path
from . import views

urlpatterns = [
	path('', views.dashboard, name='dashboard'),
	path('hotels/new/', views.hotel_create, name='hotel_create'),
	path('hotels/<int:pk>/edit/', views.hotel_edit, name='hotel_edit'),
	path('evaluations/new/', views.evaluation_create, name='evaluation_create'),
	path('evaluations/<int:pk>/', views.evaluation_detail, name='evaluation_detail'),
	path('evaluations/<int:pk>/edit/', views.evaluation_edit, name='evaluation_edit'),
	path('evaluations/<int:pk>/print/', views.report_print, name='report_print'),
]
