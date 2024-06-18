from django.contrib import admin
from django.urls import path, include
from asistencia import views
from .views import Index, LockScreen

urlpatterns = [

    path('login/', views.login_view, name='login'),
    path('agregar_usuario/', views.agregar_usuario, name='agregar_usuario'),
    path('lista_usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('editar_usuario/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('eliminar_usuario/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('generar_qr/', views.generar_qr_view, name='generar_qr'),
    path('escanear_qr/', views.escanear_qr_view, name='escanear_qr'),
    path('home/', views.home_view, name='home'),  # Home view
    path('', LockScreen.as_view(), name='lock_screen'),
    path('index/', views.Index.as_view(), name='index'),
    # Otras rutas
]
