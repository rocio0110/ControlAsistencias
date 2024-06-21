from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
import qrcode
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import Usuarios, Asistencia  # Asegúrate de importar tus modelos personalizados
from .forms import UsuarioForm  # Asumiendo que has creado un formulario para el modelo Usuarios

from io import BytesIO
import base64

from django.conf import settings

# Funciones de vista basadas en funciones

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
    # Lógica para la vista de inicio si es necesario
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

# @login_required
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


# Vistas basadas en clases

class Index(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'index.html')


class BasicTable(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'basic_table.html')


class ResponsiveTable(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'responsive_table.html')

class LockScreen(View):
    def get(self, request):
        return render(request, 'lock_screen.html')


# Otras vistas

@login_required
def generar_qr_view(request):
    # Obtener detalles del usuario autenticado
    usuario = request.user
    usuario_id = usuario.id
    nombre_usuario = usuario.username  # o cualquier otro atributo como usuario.get_full_name()

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # Construir la URL dinámica
    domain = settings.RENDER_EXTERNAL_HOSTNAME or 'http://127.0.0.1:8000'
    qr_url = f'{domain}/generar_qr/{usuario_id}'
    
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)

    # Generar el nombre del archivo usando el nombre del usuario
    file_name = f'qr_codes/{nombre_usuario}_{usuario_id}.png'
    file_path = default_storage.save(file_name, ContentFile(buffer.read()))
    qr_code_url = default_storage.url(file_path)

    return render(request, 'qr.html', {'qr_code_url': qr_code_url})


@login_required
def escanear_qr_view(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id', '')

        try:
            asistencia = Asistencia.objects.get(usuario_id=usuario_id)
            asistencia.fecha_salida = timezone.now()
            asistencia.save()
            return redirect('entrada_exitosa', asistencia_id=asistencia.id)
        except Asistencia.DoesNotExist:
            return HttpResponse('Asistencia no encontrada.')

    return render(request, 'escanear_qr.html')
