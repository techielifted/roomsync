from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')), # Django Allauth URLs
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)), # Redirect root to login
    path('', include('roomsync.urls')), # Include your app's URLs
]