from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), 
    path('search_text/', views.search_text, name='search_text'),
    path('search_image/', views.search_image, name='search_image'),
]
