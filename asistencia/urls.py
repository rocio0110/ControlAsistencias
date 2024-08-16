from django.urls import path
from .views import *
from asistencia import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('BasicTable/', BasicTable.as_view(), name='basic_table'),
    path('agregar_usuario/', views.agregar_usuario, name='agregar_usuario'),
    path('lista_usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('editar_usuario/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('eliminar_usuario/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('home/', views.home_view, name='home'),  # Home view
    path('', LockScreen.as_view(), name='lock_screen'),
    path('admin_dashboard/', admin_dashboard_view, name='admin_dashboard'),
    
   

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
