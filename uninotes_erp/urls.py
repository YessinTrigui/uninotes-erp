from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('enrollment/', include('enrollment.urls')),
    path('dashboard/', accounts_views.dashboard_redirect_view, name='dashboard'),
    path('', accounts_views.login_view, name='home'),
]
