from django.urls import path
from .views import *
from asistencia import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path



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
    path('dashboard_prestador/', dashboard_prestador, name='dashboard_prestador'),
    path('generar_qr/<str:tipo_qr>/', views.generar_qr, name='generar_qr'),
    path('inicio/', views.inicio_prestador, name='inicio'),
    path('reportes_horas/', views.reportes_horas, name='reportes_horas'),
    path('procesar_qr/<int:qr_id>/', procesar_qr, name='procesar_qr'),
    path('entrada_exitosa/', entrada_exitosa, name='entrada_exitosa'),
    path('salida_exitosa/', salida_exitosa, name='salida_exitosa'),
    path('inactivos/', lista_usuarios_inactivos, name='usuarios_inactivos'),
    path('marcar_inactivo/<int:usuario_id>/', marcar_usuario_inactivo, name='marcar_usuario_inactivo'),
    path('descargar_reporte_pdf/', descargar_reporte_pdf, name='descargar_reporte_pdf'),
    path('escanear-qr/', scan_qr_view, name='scan_qr'),
    path('registrar-asistencia/', registrar_asistencia, name='registrar_asistencia'),
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)