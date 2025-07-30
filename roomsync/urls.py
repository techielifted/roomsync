from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('book_slot/', views.book_slot_api, name='book_slot_api'),
    path('admin_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
]