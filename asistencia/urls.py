from django.urls import path
from .views import *
from asistencia import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('BasicTable/', BasicTable.as_view(), name='basic_table'),
    path('agregar_usuario/', views.agregar_usuario, name='agregar_usuario'),
    path('lista_usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('editar_usuario/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('eliminar_usuario/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('generar_qr/', views.generar_qr_view, name='generar_qr'),
    path('escanear_qr/', views.escanear_qr_view, name='escanear_qr'),
    path('home/', views.home_view, name='home'),  # Home view
    path('entrada_exitosa/<int:asistencia_id>/', views.entrada_exitosa_view, name='entrada_exitosa'),
    path('registrar_asistencia/<int:usuario_id>/', views.registrar_asistencia_view, name='registrar_asistencia'),
    path('', LockScreen.as_view(), name='lock_screen'),
    path('index/', views.Index.as_view(), name='index') 
]