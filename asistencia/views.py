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
from .forms import UsuarioForm
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from .models import Usuario, Asistencia

@login_required
def escanear_qr_view(request):
    error = None
    asistencia_actual = None
    todas_asistencias = None

    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        try:
            usuario = get_object_or_404(Usuario, id=usuario_id)
            asistencia_actual = Asistencia.objects.filter(usuario=usuario, fecha_salida__isnull=True).first()
            todas_asistencias = Asistencia.objects.filter(usuario=usuario).order_by('-fecha_entrada')
        except Usuario.DoesNotExist:
            error = "Usuario no encontrado"

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
            usuario = form.save()

            # Enviar correo con usuario y contraseña
            send_mail(
                'Usuario creado',
                f'Tu usuario es {usuario.user.username} y tu contraseña es {usuario.user.password}',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.correo_electronico],
                fail_silently=False,
            )

            messages.success(request, 'Usuario agregado correctamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm()
    return render(request, 'agregar_usuario.html', {'form': form})

# @login_required
def lista_usuarios(request):
    usuario = Usuario.objects.all()
    query = request.GET.get('q')
    if query:
        usuario = usuario.filter(nombre__icontains=query)
    return render(request, 'lista_usuarios.html', {'usuario': usuario, 'query': query})

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
    usuario = request.user.usuario

    # Generar QR de entrada
    qr_entrada = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    domain = settings.RENDER_EXTERNAL_HOSTNAME or 'http://127.0.0.1:8000'
    qr_entrada_url = f'{domain}/registrar_asistencia/{usuario.id}/entrada'
    qr_entrada.add_data(qr_entrada_url)
    qr_entrada.make(fit=True)
    img_entrada = qr_entrada.make_image(fill='black', back_color='white')

    buffer_entrada = BytesIO()
    img_entrada.save(buffer_entrada, 'PNG')
    buffer_entrada.seek(0)
    file_name_entrada = f'qr_codes/entrada_{usuario.id}.png'
    file_path_entrada = default_storage.save(file_name_entrada, ContentFile(buffer_entrada.read()))
    qr_code_entrada_url = default_storage.url(file_path_entrada)

    # Generar QR de salida (solo si han pasado 4 horas)
    qr_salida_url = ''
    if usuario.asistencia_set.filter(fecha_salida__isnull=True).exists():
        asistencia = usuario.asistencia_set.filter(fecha_salida__isnull=True).first()
        tiempo_transcurrido = timezone.now() - asistencia.fecha_entrada
        if tiempo_transcurrido >= timedelta(hours=4):
            qr_salida = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr_salida_url = f'{domain}/registrar_asistencia/{usuario.id}/salida'
            qr_salida.add_data(qr_salida_url)
            qr_salida.make(fit=True)
            img_salida = qr_salida.make_image(fill='black', back_color='white')

            buffer_salida = BytesIO()
            img_salida.save(buffer_salida, 'PNG')
            buffer_salida.seek(0)
            file_name_salida = f'qr_codes/salida_{usuario.id}.png'
            file_path_salida = default_storage.save(file_name_salida, ContentFile(buffer_salida.read()))
            qr_code_salida_url = default_storage.url(file_path_salida)

    return render(request, 'qr.html', {'qr_code_entrada_url': qr_code_entrada_url, 'qr_code_salida_url': qr_code_salida_url})

@login_required
def registrar_asistencia_view(request, usuario_id, tipo):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    if tipo == 'entrada':
        Asistencia.objects.create(
            usuario=usuario,
            fecha_entrada=timezone.now(),
        )
    elif tipo == 'salida':
        asistencia = Asistencia.objects.filter(usuario=usuario, fecha_salida__isnull=True).first()
        if asistencia:
            asistencia.fecha_salida = timezone.now()
            asistencia.save()

            # Calcular horas trabajadas y actualizar usuario
            horas_trabajadas = (asistencia.fecha_salida - asistencia.fecha_entrada).total_seconds() / 3600
            usuario.horas_realizadas += horas_trabajadas
            usuario.save()

            # Verificar si faltan 20 horas para completar el servicio/residencia
            if usuario.horas_requeridas - usuario.horas_realizadas <= 20:
                send_mail(
                    'Servicio/Residencia casi completo',
                    f'Hola {usuario.nombre}, te faltan menos de 20 horas para completar tu {usuario.tipo_servicio}.',
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.correo_electronico],
                    fail_silently=False,
                )

    return redirect('entrada_exitosa', asistencia_id=asistencia.id)

@login_required
def entrada_exitosa_view(request, asistencia_id):
    asistencia = get_object_or_404(Asistencia, id=asistencia_id)
    return render(request, 'entrada_exitosa.html', {'asistencia': asistencia})

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
    
    return render(request, 'dashboard.html', context)

# from django.shortcuts import render, get_object_or_404, redirect
# from django.urls import reverse_lazy
# from django.contrib.auth.decorators import login_required
# from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
# from django.contrib.auth.mixins import LoginRequiredMixin
# from .models import Usuario, PerfilUsuario, Asistencia, Mensaje, Reporte, LogActividad
# from .forms import UsuarioForm, PerfilUsuarioForm, AsistenciaForm, MensajeForm, ReporteForm, CustomAuthenticationForm
# from django.contrib import messages
# from django.utils import timezone
# from django.contrib.auth import authenticate, login
# from django.http import HttpResponse, JsonResponse
# from io import BytesIO
# import qrcode
# from django.core.mail import send_mail
# from django.conf import settings

# def custom_login_view(request):
#     if request.method == 'POST':
#         form = CustomAuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             username = form.cleaned_data.get('username')
#             password = form.cleaned_data.get('password')
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 if user.tipo_usuario in ['servicio_social', 'residencia']:
#                     login(request, user)
#                     return redirect('index')  # Redirige a la página principal después del login
#                 else:
#                     form.add_error(None, 'Solo usuarios de servicio social y residencia pueden iniciar sesión aquí.')
#             else:
#                 form.add_error(None, 'Nombre de usuario o contraseña incorrectos.')
#     else:
#         form = CustomAuthenticationForm()

#     return render(request, 'login.html', {'form': form})

# def generate_qr_code(request, asistencia_id):
#     asistencia = get_object_or_404(Asistencia, pk=asistencia_id)
#     qr_data = f"{request.build_absolute_uri('/register_attendance/')}{asistencia.id}"
#     qr = qrcode.QRCode(
#         version=1,
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         box_size=10,
#         border=4,
#     )
#     qr.add_data(qr_data)
#     qr.make(fit=True)
#     img = qr.make_image(fill='black', back_color='white')
#     buffer = BytesIO()
#     img.save(buffer)
#     buffer.seek(0)
#     return HttpResponse(buffer, content_type='image/png')

# def register_attendance(request, asistencia_id):
#     asistencia = get_object_or_404(Asistencia, pk=asistencia_id)
#     if not asistencia.asistencia_confirmada:
#         asistencia.asistencia_confirmada = True
#         asistencia.save()
#         return JsonResponse({'status': 'success', 'message': 'Asistencia registrada exitosamente.'})
#     else:
#         return JsonResponse({'status': 'error', 'message': 'La asistencia ya ha sido registrada.'})

# def asistencia_detail(request, asistencia_id):
#     asistencia = get_object_or_404(Asistencia, pk=asistencia_id)
#     return render(request, 'asistencia/asistencia_detail.html', {'asistencia': asistencia})

# class Index(LoginRequiredMixin, View):
#     def get(self, request):
#         return render(request, 'index.html')

# class BasicTable(LoginRequiredMixin, View):
#     def get(self, request):
#         return render(request, 'basic_table.html')

# class ResponsiveTable(LoginRequiredMixin, View):
#     def get(self, request):
#         return render(request, 'responsive_table.html')

# class GestionarUsuarios(LoginRequiredMixin, View):
#     def get(self, request):
#         return render(request, 'gestionar_usuarios.html')

# class Calendar(LoginRequiredMixin, View):
#     def get(self, request):
#         return render(request, 'calendar.html')

# class LockScreen(View):
#     def get(self, request):
#         return render(request, 'lock_screen.html')

# class UsuarioListView(LoginRequiredMixin, ListView):
#     model = Usuario
#     template_name = 'usuarios/usuario_list.html'
#     context_object_name = 'usuarios'

# class UsuarioDetailView(LoginRequiredMixin, DetailView):
#     model = Usuario
#     template_name = 'usuarios/usuario_detail.html'

# class UsuarioCreateView(LoginRequiredMixin, CreateView):
#     model = Usuario
#     form_class = UsuarioForm
#     template_name = 'usuarios/usuario_form.html'
#     success_url = reverse_lazy('usuario_list')
    
#     def form_valid(self, form):
#         response = super().form_valid(form)
#         usuario = form.instance
#         # Generar credenciales
#         nombre_usuario = usuario.nombre.lower()
#         contrasena = (usuario.apellido_paterno[:2] + usuario.apellido_materno[:2]).lower()
        
#         # Establecer el nombre de usuario y la contraseña
#         usuario.nombre_usuario = nombre_usuario
#         usuario.set_password(contrasena)
#         usuario.save()
        
#         # Enviar correo electrónico con las credenciales
#         send_mail(
#             'Credenciales de acceso',
#             f'Nombre de usuario: {nombre_usuario}\nContraseña: {contrasena}',
#             settings.DEFAULT_FROM_EMAIL,
#             [usuario.correo_electronico],
#             fail_silently=False,
#         )
        
#         return response

        
# class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
#     model = Usuario
#     form_class = UsuarioForm
#     template_name = 'usuarios/usuario_form.html'
#     success_url = reverse_lazy('usuario_list')

# class UsuarioDeleteView(LoginRequiredMixin, DeleteView):
#     model = Usuario
#     template_name = 'usuarios/usuario_confirm_delete.html'
#     success_url = reverse_lazy('usuario_list')

# @login_required
# def perfil_list(request):
#     perfiles = PerfilUsuario.objects.all()
#     return render(request, 'perfiles/perfil_list.html', {'perfiles': perfiles})

# @login_required
# def perfil_detail(request, pk):
#     perfil = get_object_or_404(PerfilUsuario, pk=pk)
#     return render(request, 'perfiles/perfil_detail.html', {'perfil': perfil})

# @login_required
# def perfil_create(request):
#     if request.method == "POST":
#         form = PerfilUsuarioForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('perfil_list')
#     else:
#         form = PerfilUsuarioForm()
#     return render(request, 'perfiles/perfil_form.html', {'form': form})

# @login_required
# def perfil_update(request, pk):
#     perfil = get_object_or_404(PerfilUsuario, pk=pk)
#     if request.method == "POST":
#         form = PerfilUsuarioForm(request.POST, instance=perfil)
#         if form.is_valid():
#             form.save()
#             return redirect('perfil_detail', pk=pk)
#     else:
#         form = PerfilUsuarioForm(instance=perfil)
#     return render(request, 'perfiles/perfil_form.html', {'form': form})

# @login_required
# def perfil_delete(request, pk):
#     perfil = get_object_or_404(PerfilUsuario, pk=pk)
#     if request.method == "POST":
#         perfil.delete()
#         return redirect('perfil_list')
#     return render(request, 'perfiles/perfil_confirm_delete.html', {'perfil': perfil})

# @login_required
# def asistencia_list(request):
#     asistencias = Asistencia.objects.all()
#     return render(request, 'asistencias/asistencia_list.html', {'asistencias': asistencias})

# @login_required
# def asistencia_detail(request, pk):
#     asistencia = get_object_or_404(Asistencia, pk=pk)
#     return render(request, 'asistencias/asistencia_detail.html', {'asistencia': asistencia})

# @login_required
# def asistencia_create(request):
#     if request.method == "POST":
#         form = AsistenciaForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('asistencia_list')
#     else:
#         form = AsistenciaForm()
#     return render(request, 'asistencias/asistencia_form.html', {'form': form})

# @login_required
# def asistencia_update(request, pk):
#     asistencia = get_object_or_404(Asistencia, pk=pk)
#     if request.method == "POST":
#         form = AsistenciaForm(request.POST, instance=asistencia)
#         if form.is_valid():
#             form.save()
#             return redirect('asistencia_detail', pk=pk)
#     else:
#         form = AsistenciaForm(instance=asistencia)
#     return render(request, 'asistencias/asistencia_form.html', {'form': form})

# @login_required
# def asistencia_delete(request, pk):
#     asistencia = get_object_or_404(Asistencia, pk=pk)
#     if request.method == "POST":
#         asistencia.delete()
#         return redirect('asistencia_list')
#     return render(request, 'asistencias/asistencia_confirm_delete.html', {'asistencia': asistencia})

# @login_required
# def mensaje_list(request):
#     mensajes = Mensaje.objects.all()
#     return render(request, 'mensajes/mensaje_list.html', {'mensajes': mensajes})

# @login_required
# def mensaje_detail(request, pk):
#     mensaje = get_object_or_404(Mensaje, pk=pk)
#     return render(request, 'mensajes/mensaje_detail.html', {'mensaje': mensaje})

# @login_required
# def mensaje_create(request):
#     if request.method == "POST":
#         form = MensajeForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('mensaje_list')
#     else:
#         form = MensajeForm()
#     return render(request, 'mensajes/mensaje_form.html', {'form': form})

# @login_required
# def mensaje_update(request, pk):
#     mensaje = get_object_or_404(Mensaje, pk=pk)
#     if request.method == "POST":
#         form = MensajeForm(request.POST, instance=mensaje)
#         if form.is_valid():
#             form.save()
#             return redirect('mensaje_detail', pk=pk)
#     else:
#         form = MensajeForm(instance=mensaje)
#     return render(request, 'mensajes/mensaje_form.html', {'form': form})

# @login_required
# def mensaje_delete(request, pk):
#     mensaje = get_object_or_404(Mensaje, pk=pk)
#     if request.method == "POST":
#         mensaje.delete()
#         return redirect('mensaje_list')
#     return render(request, 'mensajes/mensaje_confirm_delete.html', {'mensaje': mensaje})

# @login_required
# def reporte_list(request):
#     reportes = Reporte.objects.all()
#     return render(request, 'reportes/reporte_list.html', {'reportes': reportes})

# @login_required
# def reporte_detail(request, pk):
#     reporte = get_object_or_404(Reporte, pk=pk)
#     return render(request, 'reportes/reporte_detail.html', {'reporte': reporte})

# @login_required
# def reporte_create(request):
#     if request.method == "POST":
#         form = ReporteForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('reporte_list')
#     else:
#         form = ReporteForm()
#     return render(request, 'reportes/reporte_form.html', {'form': form})

# @login_required
# def reporte_update(request, pk):
#     reporte = get_object_or_404(Reporte, pk=pk)
#     if request.method == "POST":
#         form = ReporteForm(request.POST, instance=reporte)
#         if form.is_valid():
#             form.save()
#             return redirect('reporte_detail', pk=pk)
#     else:
#         form = ReporteForm(instance=reporte)
#     return render(request, 'reportes/reporte_form.html', {'form': form})

# @login_required
# def reporte_delete(request, pk):
#     reporte = get_object_or_404(Reporte, pk=pk)
#     if request.method == "POST":
#         reporte.delete()
#         return redirect('reporte_list')
#     return render(request, 'reportes/reporte_confirm_delete.html', {'reporte': reporte})

# def log_list(request):
#     logs = LogActividad.objects.all()
#     return render(request, 'logs/log_list.html', {'logs': logs})

# from django.shortcuts import render, get_object_or_404
# from .models import LogActividad

# def log_detail(request, pk):
#     log = get_object_or_404(LogActividad, pk=pk)
#     return render(request, 'logs/log_detail.html', {'log': log})
