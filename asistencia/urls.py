
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
    path('index/', views.Index.as_view(), name='index'),
    path('escanear/', escanear_qr_view, name='escanear_qr'), 
    path('gestionar_usuarios/', GestionarUsuarios.as_view(), name='gestionar_usuarios'), 
    path('calendar/', Calendar.as_view(), name='calendar'), 
    path('reporte/', generar_reporte_view, name='reporte'),
    path('reporte/pdf/', generar_reporte_pdf_view, name='reporte_pdf'),
    
]


# from django.urls import path
# from .views import *
# from . import views


# urlpatterns = [

#     path('generate_qr_code/<int:asistencia_id>/', generate_qr_code, name='generate_qr_code'),
#     path('register_attendance/<int:asistencia_id>/', register_attendance, name='register_attendance'),
#     # Vistas principales
#     path('', LockScreen.as_view(), name='lock_screen'),
#     path('index/', Index.as_view(), name='index'),
#     path('basic_table/', BasicTable.as_view(), name='basic_table'),
#     path('responsive_table/', ResponsiveTable.as_view(), name='responsive_table'),
#     path('gestionar_usuarios/', GestionarUsuarios.as_view(), name='gestionar_usuarios'),
#     path('calendar/', Calendar.as_view(), name='calendar'),
#     path('login/', custom_login_view, name='login'),

#     # Vistas para Usuario
#     path('usuarios/', UsuarioListView.as_view(), name='usuario_list'),
#     path('usuarios/<int:pk>/', UsuarioDetailView.as_view(), name='usuario_detail'),
#     path('usuarios/create/', UsuarioCreateView.as_view(), name='usuario_create'),
#     path('usuarios/<int:pk>/edit/', UsuarioUpdateView.as_view(), name='usuario_update'),
#     path('usuarios/<int:pk>/delete/', UsuarioDeleteView.as_view(), name='usuario_delete'),

#     # Vistas para PerfilUsuario
#     path('perfiles/', perfil_list, name='perfil_list'),
#     path('perfiles/<int:pk>/', perfil_detail, name='perfil_detail'),
#     path('perfiles/create/', perfil_create, name='perfil_create'),
#     path('perfiles/<int:pk>/edit/', perfil_update, name='perfil_update'),
#     path('perfiles/<int:pk>/delete/', perfil_delete, name='perfil_delete'),

#     # Vistas para Asistencia
#     path('asistencias/', asistencia_list, name='asistencia_list'),
#     path('asistencias/<int:pk>/', asistencia_detail, name='asistencia_detail'),
#     path('asistencias/create/', asistencia_create, name='asistencia_create'),
#     path('asistencias/<int:pk>/edit/', asistencia_update, name='asistencia_update'),
#     path('asistencias/<int:pk>/delete/', asistencia_delete, name='asistencia_delete'),

#     # Vistas para Mensaje
#     path('mensajes/', mensaje_list, name='mensaje_list'),
#     path('mensajes/<int:pk>/', mensaje_detail, name='mensaje_detail'),
#     path('mensajes/create/', mensaje_create, name='mensaje_create'),
#     path('mensajes/<int:pk>/edit/', mensaje_update, name='mensaje_update'),
#     path('mensajes/<int:pk>/delete/', mensaje_delete, name='mensaje_delete'),

#     # Vistas para Reporte
#     path('reportes/', reporte_list, name='reporte_list'),
#     path('reportes/<int:pk>/', reporte_detail, name='reporte_detail'),
#     path('reportes/create/', reporte_create, name='reporte_create'),
#     path('reportes/<int:pk>/edit/', reporte_update, name='reporte_update'),
#     path('reportes/<int:pk>/delete/', reporte_delete, name='reporte_delete'),

#     # Vistas para LogActividad
#     path('logs/', log_list, name='log_list'),
#     path('logs/<int:pk>/', log_detail, name='log_detail'),
# ]
