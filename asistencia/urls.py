from django.urls import path
from .views import *

urlpatterns = [
    # path('', admin.site.urls),
    path('login/', login_view, name='login'),
    path('BasicTable/', BasicTable.as_view(), name='basic_table'),  # Asegúrate de llamar al método as_view()
    path('agregar_usuario/', agregar_usuario, name='agregar_usuario'),
    path('lista_usuarios/', lista_usuarios, name='lista_usuarios'),
    path('editar_usuario/<int:pk>/', editar_usuario, name='editar_usuario'),
    path('eliminar_usuario/<int:pk>/', eliminar_usuario, name='eliminar_usuario'),
    path('generar_qr/', generar_qr_view, name='generar_qr'),
    path('escanear_qr/', escanear_qr_view, name='escanear_qr'),
    path('home/', home_view, name='home'),
    path('', LockScreen.as_view(), name='lock_screen'),  # Home view
    path('index/', Index.as_view(), name='index'),
]
