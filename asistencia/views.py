from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.conf import settings
from .models import Usuarios, Asistencia
from .forms import UsuarioForm
import qrcode
from io import BytesIO
from datetime import datetime

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('generar_qr')  # Redirige a donde quieras después del login exitoso
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def home_view(request):
    return render(request, 'home.html')

def agregar_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario agregado correctamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm()
    return render(request, 'agregar_usuario.html', {'form': form})

@login_required
def lista_usuarios(request):
    usuarios = Usuarios.objects.all()
    query = request.GET.get('q')
    if query:
        usuarios = usuarios.filter(nombre__icontains=query)
    return render(request, 'lista_usuarios.html', {'usuarios': usuarios, 'query': query})

@login_required
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuarios, pk=pk)
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
    usuario = get_object_or_404(Usuarios, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('lista_usuarios')
    return render(request, 'eliminar_usuario.html', {'usuario': usuario})

class Index(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'index.html')

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

@login_required
def generar_qr_view(request):
    usuario = request.user
    usuario_id = usuario.id
    nombre_usuario = usuario.username

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    domain = settings.RENDER_EXTERNAL_HOSTNAME or 'http://127.0.0.1:8000'
    qr_url = f'{domain}/registrar_asistencia/{usuario_id}'
    
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)

    file_name = f'qr_codes/{nombre_usuario}_{usuario_id}.png'
    file_path = default_storage.save(file_name, ContentFile(buffer.read()))
    qr_code_url = default_storage.url(file_path)

    return render(request, 'qr.html', {'qr_code_url': qr_code_url})

@login_required
def entrada_exitosa_view(request, asistencia_id):
    asistencia = get_object_or_404(Asistencia, id=asistencia_id)
    return render(request, 'entrada_exitosa.html', {'asistencia': asistencia})

@login_required
def escanear_qr_view(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id', '')

        try:
            # Filtrar todas las asistencias activas del usuario
            asistencias_activas = Asistencia.objects.filter(usuario_id=usuario_id, fecha_salida__isnull=True)

            # Asegúrate de que solo haya una asistencia activa (debería ser solo una)
            if asistencias_activas.exists():
                asistencia_actual = asistencias_activas.first()

                # Actualizar la fecha de salida y guardar la asistencia
                asistencia_actual.fecha_salida = timezone.now()
                asistencia_actual.save()

                # Calcular horas trabajadas y actualizar usuario
                horas_trabajadas = (asistencia_actual.fecha_salida - asistencia_actual.fecha_entrada).total_seconds() / 3600
                usuario = asistencia_actual.usuario
                usuario.horas_realizadas += horas_trabajadas
                usuario.save()

                # Enviar correo electrónico
                enviar_correo_asistencia(usuario)

                # Obtener todas las asistencias del usuario
                todas_asistencias = Asistencia.objects.filter(usuario_id=usuario_id)

                return render(request, 'escanear_qr.html', {'asistencia_actual': asistencia_actual, 'todas_asistencias': todas_asistencias})
            else:
                error = 'No se encontró ninguna asistencia activa para este usuario.'
                return render(request, 'escanear_qr.html', {'error': error})
        
        except Asistencia.DoesNotExist:
            error = 'Asistencia no encontrada.'
            return render(request, 'escanear_qr.html', {'error': error})

    return render(request, 'escanear_qr.html')


@login_required
def registrar_asistencia_view(request, usuario_id):
    usuario = get_object_or_404(Usuarios, id=usuario_id)
    asistencia = Asistencia.objects.create(
        usuario=usuario,
        fecha_entrada=timezone.now(),
    )

    # Enviar correo electrónico
    enviar_correo_asistencia(usuario)

    return redirect('entrada_exitosa', asistencia_id=asistencia.id)

def enviar_correo_asistencia(usuario):
    send_mail(
        'Registro de Asistencia Exitoso',
        f'Hola {usuario.username}, tu asistencia ha sido registrada exitosamente.',
        settings.DEFAULT_FROM_EMAIL,
        [usuario.email],
        fail_silently=False,
    )


from django.shortcuts import render, get_object_or_404
from .models import Asistencia

def revisar_asistencia(request):
    if request.method == 'POST':
        nombre_usuario = request.POST.get('nombre_usuario')

        if not nombre_usuario:
            error = "Por favor, ingresa un nombre de usuario válido."
            return render(request, 'escanear_qr.html', {'error': error})

        try:
            # Buscar la asistencia por nombre de usuario
            asistencia_actual = Asistencia.objects.get(usuario__nombre=nombre_usuario)
            todas_asistencias = Asistencia.objects.filter(usuario__nombre=nombre_usuario)
            
            return render(request, 'escanear_qr.html', {'asistencia_actual': asistencia_actual, 'todas_asistencias': todas_asistencias})

        except Asistencia.DoesNotExist:
            error = f"No se encontró asistencia para el usuario con nombre {nombre_usuario}."
            return render(request, 'escanear_qr.html', {'error': error})

    return render(request, 'escanear_qr.html')

from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from .models import Asistencia

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