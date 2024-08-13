

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
import segno
from io import BytesIO
from datetime import datetime, timedelta
from .models import Usuario, Asistencia
from django.contrib.auth.models import User
import random
import string
import os


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



@login_required
def escanear_qr_view(request):
    error = None
    asistencia_actual = None
    todas_asistencias = None

    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        if usuario_id is not None and usuario_id.isdigit():
            try:
                usuario = get_object_or_404(Usuario, id=usuario_id)
                asistencia_actual = Asistencia.objects.filter(usuario=usuario, fecha_salida__isnull=True).first()
                todas_asistencias = Asistencia.objects.filter(usuario=usuario).order_by('-fecha_entrada')
            except Usuario.DoesNotExist:
                error = "Usuario no encontrado"
        else:
            error = "ID de usuario inválido"

    return render(request, 'escanear_qr.html', {
        'error': error,
        'asistencia_actual': asistencia_actual,
        'todas_asistencias': todas_asistencias,
    })

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)  # Usa auth_login en lugar de login
            if user.is_superuser:
                return redirect('admin_dashboard')  #nombre de la URL 
            else:
                return redirect('generar_qr')  # Redirige a donde quieras para usuarios normales
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

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

from django.db import IntegrityError

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

            username = nombre
            password = generate_password(nombre, apellido_paterno, apellido_materno)

            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya está en uso.')
                return render(request, 'agregar_usuario.html', {'form': form})

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

            subject = 'Tu cuenta ha sido creada'
            message = f'Hola {nombre},\n\nTu cuenta ha sido creada con éxito.\n\nNombre de usuario: {username}\nContraseña: {password}\n\nSaludos,\nEl equipo de Control de Asistencias'
            from_email = settings.DEFAULT_FROM_EMAIL
            send_mail(subject, message, from_email, [correo_electronico])

            messages.success(request, 'Usuario agregado exitosamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm()

    return render(request, 'agregar_usuario.html', {'form': form})



import logging

logger = logging.getLogger(__name__)


from django.db.models import Sum
from datetime import timedelta

@login_required
def lista_usuarios(request):
    usuarios = Usuario.objects.all()
    query = request.GET.get('q')
    if query:
        usuarios = usuarios.filter(nombre__icontains=query)

    for usuario in usuarios:
        try:
            # Inicializar horas realizadas
            horas_realizadas = 0
            asistencias = Asistencia.objects.filter(usuario=usuario, fecha_salida__isnull=False)
            for asistencia in asistencias:
                if asistencia.fecha_salida and asistencia.fecha_entrada:
                    delta = asistencia.fecha_salida - asistencia.fecha_entrada
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



@login_required
def generar_qr_view(request):
    try:
        usuario = request.user.usuario
    except Usuario.DoesNotExist:
        messages.error(request, "Tu perfil de usuario no está configurado correctamente.")
        return redirect('home')

    qr_code_entrada_url = None
    qr_code_salida_url = None

    # Define the correct media directory for saving QR codes
    qr_code_media_path = os.path.join(settings.MEDIA_ROOT, 'img')

    # Verifica y crea el directorio si no existe
    os.makedirs(qr_code_media_path, exist_ok=True)

    file_name_entrada = f'entrada_{usuario.id}_{timezone.now().date()}.png'
    entrada_generada = os.path.exists(os.path.join(qr_code_media_path, file_name_entrada))

    if entrada_generada:
        messages.info(request, "Ya has generado un QR de entrada para hoy.")
        qr_code_entrada_url = os.path.join(settings.MEDIA_URL, f'img/{file_name_entrada}')
    else:
        # Generate and save the entry QR code using segno
        domain = settings.RENDER_EXTERNAL_HOSTNAME or 'http://127.0.0.1:8000'
        qr_entrada_url = f'{domain}/registro_exitoso/{usuario.id}/entrada'

        qr_entrada = segno.make(qr_entrada_url)
        qr_entrada.save(os.path.join(qr_code_media_path, file_name_entrada))
        qr_code_entrada_url = os.path.join(settings.MEDIA_URL, f'img/{file_name_entrada}')

    file_name_salida = f'salida_{usuario.id}_{timezone.now().date()}.png'
    salida_generada = os.path.exists(os.path.join(qr_code_media_path, file_name_salida))

    if salida_generada:
        messages.info(request, "Ya has generado un QR de salida para hoy.")
        qr_code_salida_url = os.path.join(settings.MEDIA_URL, f'img/{file_name_salida}')
    elif usuario.asistencia_set.filter(fecha_salida__isnull=True, fecha_entrada__date=timezone.now().date()).exists():
        asistencia = usuario.asistencia_set.filter(fecha_salida__isnull=True, fecha_entrada__date=timezone.now().date()).first()
        tiempo_transcurrido = timezone.now() - asistencia.fecha_entrada
        if tiempo_transcurrido >= timedelta(hours=4):
            # Generate and save the exit QR code using segno
            qr_salida_url = f'{domain}/registro_exitoso/{usuario.id}/salida'

            qr_salida = segno.make(qr_salida_url)
            qr_salida.save(os.path.join(qr_code_media_path, file_name_salida))
            qr_code_salida_url = os.path.join(settings.MEDIA_URL, f'img/{file_name_salida}')

    return render(request, 'qr.html', {
        'qr_code_entrada_url': qr_code_entrada_url,
        'qr_code_salida_url': qr_code_salida_url
    })

@login_required
def registrar_asistencia_view(request, usuario_id, tipo):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    if tipo == 'entrada':
        if Asistencia.objects.filter(usuario=usuario, fecha_entrada__date=timezone.now().date()).exists():
            messages.error(request, 'Ya se ha registrado una entrada para hoy.')
            return redirect('generar_qr')  # Redirige al formulario de generación de QR
        asistencia = Asistencia.objects.create(
            usuario=usuario,
            fecha_entrada=timezone.now(),
        )
        return redirect('entrada_exitosa', asistencia_id=asistencia.id)
    elif tipo == 'salida':
        asistencia = Asistencia.objects.filter(usuario=usuario, fecha_salida__isnull=True).first()
        if asistencia:
            if Asistencia.objects.filter(usuario=usuario, fecha_salida__date=timezone.now().date()).exists():
                messages.error(request, 'Ya se ha registrado una salida para hoy.')
                return redirect('generar_qr')  # Redirige al formulario de generación de QR
            asistencia.fecha_salida = timezone.now()
            asistencia.save()

            # Calcular horas trabajadas y actualizar usuario
            horas_trabajadas = (asistencia.fecha_salida - asistencia.fecha_entrada).total_seconds() / 3600
            usuario.horas_realizadas += horas_trabajadas
            usuario.save()

            # Verificar si faltan 20 horas para completar el servicio/residencia
            horas_faltantes = usuario.horas_requeridas - usuario.horas_realizadas
            if horas_faltantes <= 20:
                subject = 'Advertencia: Servicio/Residencia casi completo'
                message = (
                    f'Hola {usuario.nombre},\n\n'
                    f'Te faltan menos de 20 horas para completar tu {usuario.tipo_servicio}.\n\n'
                    f'¡Sigue así!\n\n'
                    f'Saludos,\n'
                    f'El equipo de Control de Asistencias'
                )
                from_email = settings.DEFAULT_FROM_EMAIL
                send_mail(subject, message, from_email, [usuario.correo_electronico])

                # Enviar correo al administrador
                send_mail(
                    subject,
                    f'El usuario {usuario.nombre} está a punto de completar su {usuario.tipo_servicio}. Faltan {horas_faltantes} horas.',
                    from_email,
                    [settings.ADMIN_EMAIL]  # Asumiendo que ADMIN_EMAIL está configurado en settings
                )
        return redirect('entrada_exitosa', asistencia_id=asistencia.id)


@login_required
def entrada_exitosa_view(request, asistencia_id):
    asistencia = get_object_or_404(Asistencia, id=asistencia_id)
    
    if asistencia.fecha_salida:
        # Es una salida
        return render(request, 'salida_exitosa.html', {'asistencia': asistencia})
    else:
        # Es una entrada
        hora_salida_aproximada = asistencia.fecha_entrada + timedelta(hours=4)
        return render(request, 'entrada_exitosa.html', {
            'asistencia': asistencia,
            'hora_salida_aproximada': hora_salida_aproximada
        })



@login_required
def generar_reporte_pdf_view(request):
    asistencias = Asistencia.objects.all()
    template_path = 'reporte_asistencias.html'
    context = {'asistencias': asistencias}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_asistencias.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF: %s' % pisa_status.err, status=500)
    
    return response

@login_required
def generar_reporte_view(request):
    asistencias = Asistencia.objects.all()
    context = {'asistencias': asistencias}
    return render(request, 'reporte_asistencias.html', context)

@login_required
def dashboard_view(request):
    # Obtener datos de asistencia
    asistencias = Asistencia.objects.all()

    # Procesar datos para gráficos
    fechas = [a.fecha_entrada.strftime('%Y-%m-%d') for a in asistencias]
    conteos = Asistencia.objects.values('fecha_entrada').annotate(conteo=Count('id'))

    fechas_conteo = [c['fecha_entrada'].strftime('%Y-%m-%d') for c in conteos]
    conteos_diarios = [c['conteo'] for c in conteos]

    context = {
        'fechas': json.dumps(fechas_conteo),
        'conteos_diarios': json.dumps(conteos_diarios),
    }
    
    return render(request, 'admin_dashboard.html', context)
