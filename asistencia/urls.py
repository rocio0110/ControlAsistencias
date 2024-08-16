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
    path('generar_qr/', views.generar_qr_view, name='generar_qr'),
    path('escanear_qr/', views.escanear_qr_view, name='escanear_qr'),
    path('home/', views.home_view, name='home'),  # Home view
    path('', LockScreen.as_view(), name='lock_screen'),
    path('admin_dashboard/', admin_dashboard_view, name='admin_dashboard'),
    path('escanear/', escanear_qr_view, name='escanear_qr'), 
    path('gestionar_usuarios/', GestionarUsuarios.as_view(), name='gestionar_usuarios'), 
    path('calendar/', Calendar.as_view(), name='calendar'), 
    # path('reporte/', generar_reporte_view, name='reporte'),
    # path('reporte/pdf/', generar_reporte_pdf_view, name='reporte_pdf'),   
    path('registrar_asistencia/<int:usuario_id>/<str:tipo>/', registrar_asistencia_view, name='registrar_asistencia'),
    path('entrada_exitosa/<int:asistencia_id>/', entrada_exitosa_view, name='entrada_exitosa'),
    path('salida_exitosa/<int:asistencia_id>/', salida_exitosa_view, name='salida_exitosa'),


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
