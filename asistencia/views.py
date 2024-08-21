from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.conf import settings
from .forms import UsuarioForm
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from .models import Usuario
from django.contrib.auth.models import User
import random
import string
import os
import base64
import pytz
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Asistencia
from django.http import JsonResponse


def scan_qr_view(request):
    return render(request, 'scan_qr/scan_qr.html')

def registrar_asistencia(request):
    if request.method == 'POST':
        qr_data = request.POST.get('qr_data')
        
        try:
            # Supongamos que en tu QR tienes el nombre de usuario
            Usuario = Usuario.objects.get(username=qr_data)
            # Aquí puedes agregar la lógica para registrar la asistencia
            # Ejemplo:
            # Asistencia.objects.create(usuario=usuario, fecha=timezone.now())
            
            return JsonResponse({'status': 'success', 'message': 'Asistencia registrada con éxito'})
        except Usuario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Usuario no encontrado'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

    
class BasicTable(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'basic_table.html')

class ResponsiveTable(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'responsive_table.html')
    
class GestionarUsuarios(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'gestionar_usuarios.html')
    
class Calendar(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'calendar.html')
    
class LockScreen(View):
    def get(self, request):
        return render(request, 'lock_screen.html')


def generate_unique_username(base_username):
    # Asegúra de que el nombre de usuario sea único
    unique_username = base_username
    while User.objects.filter(username=unique_username).exists():
        unique_username = f"{base_username}_{random.randint(1000, 9999)}"
    return unique_username



from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponseForbidden

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_active:
                auth_login(request, user)  # Usa auth_login en lugar de login
                if user.is_superuser:
                    return redirect('admin_dashboard')  # nombre de la URL
                else:
                    return redirect('inicio')  # Redirige a donde quieras para usuarios normales
            else:
                return HttpResponseForbidden("Tu cuenta está desactivada.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def protected_view(request):
    # Verificar si el usuario está activo
    if not request.user.is_active:
        return HttpResponseForbidden("Acceso denegado")

    # Aquí va el resto del código de la vista
    # Por ejemplo, puedes renderizar una plantilla:
    context = {
        'message': '¡Bienvenido a la vista protegida!',
    }
    return render(request, 'protected_template.html', context)

class AdminDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('login')  # Redirige a la página de login si el usuario no es superusuario
        return render(request, 'admin_dashboard.html')   
    
@login_required
def home_view(request):
    return render(request, 'home.html')


def admin_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:  # Verificar si el usuario es un superusuario
                login(request, user)
                return redirect('admin_dashboard')
            else:
                form.add_error(None, "Acceso denegado. Solo los administradores pueden acceder.")
    else:
        form = AuthenticationForm()
    return render(request, 'admin_dashboard.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)  # Verificar si el usuario es un superusuario
def admin_dashboard_view(request):
    return render(request, 'admin_dashboard.html')
from django.urls import reverse

def generar_qr(request):
    user = request.user  # Obtén el usuario autenticado

    # Supongo que tienes un modelo llamado Usuario que está relacionado con User
    usuario = Usuario.objects.get(nombre=user.username)  # Filtra por el campo username

    # Datos a codificar en el QR
    qr_data = f"Usuario: {user.username}\nEmail: {user.email}\nNombre: {usuario.nombre} {usuario.apellido_paterno}"
    
    # Generar el QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir la imagen a PNG en memoria
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Preparar la respuesta de descarga
    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename=QR_{usuario.nombre}.png'
    
    return response  # Devuelve el QR como archivo descargable


from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import QR, Asistencia, Usuario

@login_required
def procesar_qr(request, qr_id):
    qr = get_object_or_404(QR, id=qr_id)
    usuario = qr.usuario

    hoy = timezone.now().date()
    asistencia = Asistencia.objects.filter(usuario=usuario, fecha_escaneo_entrada__date=hoy).first()

    if not asistencia:
        asistencia = Asistencia.objects.create(
            usuario=usuario,
            fecha_escaneo_entrada=timezone.now(),
        )
        
        # Calcula la hora de salida aproximada (asumiendo una jornada de 4 horas)
        hora_salida_aproximada = asistencia.fecha_escaneo_entrada + timedelta(hours=4)
        
        context = {
            'asistencia': asistencia,
            'hora_salida_aproximada': hora_salida_aproximada,
        }
        return render(request, 'entrada_exitosa.html', context)
    
    elif not asistencia.fecha_escaneo_salida:
        asistencia.fecha_escaneo_salida = timezone.now()
        asistencia.horas = asistencia.fecha_escaneo_salida - asistencia.fecha_escaneo_entrada
        asistencia.save()
        return redirect('salida_exitosa')

    else:
        messages.error(request, 'Ya has registrado tu entrada y salida para el día de hoy.')
        return redirect('error_view')




import random

def generate_password(nombre, apellido_paterno, apellido_materno):
    base_password = (apellido_paterno[:2] + apellido_materno[:2]).lower()
    return base_password

@login_required
def agregar_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            apellido_paterno = form.cleaned_data['apellido_paterno']
            apellido_materno = form.cleaned_data['apellido_materno']
            telefono = form.cleaned_data['telefono']
            correo_electronico = form.cleaned_data['correo_electronico']
            tipo_servicio = form.cleaned_data['tipo_servicio']

            # Generar username y contraseña
            username = nombre
            password = generate_password(nombre, apellido_paterno, apellido_materno)

            # Verificar si el nombre de usuario ya existe
            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya está en uso.')
                return render(request, 'agregar_usuario.html', {'form': form})

            # Crear el usuario de Django y el perfil asociado
            user = User.objects.create_user(username=username, password=password, email=correo_electronico)
            Usuario.objects.create(
                user=user,
                nombre=nombre,
                apellido_paterno=apellido_paterno,
                apellido_materno=apellido_materno,
                telefono=telefono,
                correo_electronico=correo_electronico,
                tipo_servicio=tipo_servicio
            )

            # Enviar email de confirmación
            subject = 'Tu cuenta ha sido creada'
            message = f'Hola {nombre},\n\nTu cuenta ha sido creada con éxito.\n\nNombre de usuario: {username}\nContraseña: {password}\n\nSaludos,\nEl equipo de Control de Asistencias'
            from_email = settings.DEFAULT_FROM_EMAIL
            send_mail(subject, message, from_email, [correo_electronico])

            messages.success(request, 'Usuario agregado exitosamente.')
            return redirect('lista_usuarios')
        else:
            messages.error(request, 'Por favor, corrija los errores a continuación.')
    else:
        form = UsuarioForm()

    return render(request, 'agregar_usuario.html', {'form': form})


def entrada_exitosa(request):
    return render(request, 'entrada_exitosa.html')  # Asegúrate de tener este template

def salida_exitosa(request):
    return render(request, 'salida_exitosa.html')  # Asegúrate de tener este template

import logging

logger = logging.getLogger(__name__)


from django.db.models import Sum
from datetime import timedelta

@login_required
def lista_usuarios(request):
    # Filtrar solo usuarios activos
    usuarios = Usuario.objects.filter(activo=True)
    
    # Manejo de búsqueda
    query = request.GET.get('q')
    if query:
        usuarios = usuarios.filter(nombre__icontains=query)
    
    # Calcular horas realizadas y horas faltantes
    for usuario in usuarios:
        try:
            horas_realizadas = 0
            asistencias = Asistencia.objects.filter(usuario=usuario, fecha_escaneo_salida__isnull=False)
            for asistencia in asistencias:
                if asistencia.fecha_escaneo_entrada and asistencia.fecha_escaneo_salida:
                    delta = asistencia.fecha_escaneo_salida - asistencia.fecha_escaneo_entrada
                    horas_realizadas += delta.total_seconds() / 3600
            
            usuario.horas_realizadas = horas_realizadas
            usuario.horas_faltantes = usuario.horas_requeridas - horas_realizadas

        except Exception as e:
            print(f"Error al calcular horas para {usuario}: {e}")
            usuario.horas_realizadas = 0
            usuario.horas_faltantes = usuario.horas_requeridas

    return render(request, 'lista_usuarios.html', {'usuarios': usuarios, 'query': query})


@login_required
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'editar_usuario.html', {'form': form})

@login_required
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('lista_usuarios')
    return render(request, 'eliminar_usuario.html', {'usuario': usuario})


# __________________________________________________________________________________
# Prestador de servicios
# __________________________________________________________________________________
def inicio_prestador(request):
    return render(request, 'prestador/inicio.html')


from django.shortcuts import render
from .models import Asistencia
from django.core.paginator import Paginator

@login_required
def reportes_horas(request):
    # Obtén la instancia de Usuario asociada al usuario autenticado
    usuario = get_object_or_404(Usuario, user=request.user)

    # Obtén las asistencias del usuario y ordénalas
    asistencias = Asistencia.objects.filter(usuario=usuario).order_by('fecha_escaneo_entrada')

    # Paginación
    paginator = Paginator(asistencias, 10)  # Mostrar 10 asistencias por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Contexto para la plantilla
    context = {
        'page_obj': page_obj,
        'now': timezone.now(),  # Agrega la fecha y hora actual al contexto
    }

    return render(request, 'prestador/reportes.html', context)

def dashboard_prestador(request):
    return render(request, 'prestador/dashboard_prestador.html')


@login_required
def marcar_usuario_inactivo(request, usuario_id):
    usuario = Usuario.objects.get(id=usuario_id)
    usuario.activo = False
    usuario.save()
    return redirect('lista_usuarios')


@login_required
def lista_usuarios_inactivos(request):
    usuarios_inactivos = Usuario.objects.filter(activo=False)
    query = request.GET.get('q')
    
    if query:
        usuarios_inactivos = usuarios_inactivos.filter(nombre__icontains=query)
    
    return render(request, 'usuarios_inactivos.html', {'usuarios': usuarios_inactivos, 'query': query})


from datetime import datetime

def descargar_reporte_pdf(request):
    # Obtener los datos de Asistencia (puedes filtrar según lo necesites)
    asistencias = Asistencia.objects.all().order_by('fecha_escaneo_entrada')
    
    # Cargar el template HTML y renderizarlo con los datos
    template = get_template('prestador/reporte_pdf.html')
    html_content = template.render({
        'asistencias': asistencias,
        'now': datetime.now(),  # Utiliza datetime directamente
    })

    # Crear una respuesta HTTP con el tipo de contenido para PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_horas.pdf"'

    # Convertir HTML a PDF usando xhtml2pdf
    pisa_status = pisa.CreatePDF(
        src=html_content.encode('utf-8'),
        dest=response,
        encoding='utf-8'
    )

    # Verificar si hubo errores en la conversión
    if pisa_status.err:
        return HttpResponse('Ocurrió un error al generar el PDF', status=400)

    return response


