from django.urls import path
from . import views

urlpatterns = [
	path('', views.home, name='face-verif-home'),
	path('info/', views.info, name='face-verif-info'),
	path('camera/', views.camera, name='face-verif-camera'),
	path('success/', views.success, name='face-verif-success'),
	path('failure/', views.failure, name='face-verif-failure'),
	path('face_verification/', views.face_verification, name='face-verification'),
	path('getData/', views.getData, name = 'get-data'),
]