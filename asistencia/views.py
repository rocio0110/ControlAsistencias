import json, random, string, qrcode, logging
from io import BytesIO
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.template.loader import get_template, render_to_string
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Sum, Count
from django.utils.dateparse import parse_date
from xhtml2pdf import pisa

from .forms import UsuarioForm
from .models import Usuario, Asistencia, QR

logger = logging.getLogger(__name__)


# ----------------- ESCANEO QR -----------------
def scan_qr_view(request):
    return render(request, 'scan_qr/scan_qr.html')
@login_required
def procesar_qr(request, tipo_qr):
    user = request.user
    usuario = Usuario.objects.get(user=user)
    hoy = timezone.now().date()

    if tipo_qr == 'entrada':
        # Verifica si ya existe un registro de entrada para hoy
        asistencia = Asistencia.objects.filter(usuario=usuario, fecha_escaneo_entrada__date=hoy).first()
        if asistencia:
            return render(request, 'error.html', {'mensaje': 'Ya registraste tu entrada hoy.'})
        
        # Registra la hora de entrada
        asistencia = Asistencia.objects.create(usuario=usuario, fecha_escaneo_entrada=timezone.now())
        
        mensaje = f"Felicidades {usuario.nombre}, tu entrada ha sido registrada."
        return render(request, 'entrada_exitosa.html', {'mensaje': mensaje, 'hora_entrada': asistencia.hora_entrada})

    elif tipo_qr == 'salida':
        # Verifica si ya existe un registro de entrada para hoy
        asistencia = Asistencia.objects.filter(usuario=usuario, fecha_escaneo_entrada__date=hoy).first()
        if not asistencia:
            return render(request, 'error.html', {'mensaje': 'No has registrado tu entrada o ya registraste tu salida.'})
        
        if asistencia.fecha_escaneo_salida:
            return render(request, 'error.html', {'mensaje': 'Ya registraste tu salida hoy.'})
        
        # Registra la hora de salida y calcula las horas trabajadas
        asistencia.fecha_escaneo_salida = timezone.now()
        asistencia.calcular_horas()
        asistencia.save()

        # Actualiza las horas realizadas en el modelo Usuario
        usuario.actualizar_horas_realizadas()

        mensaje = f"Nos vemos mañana, {usuario.nombre}. ¡Gracias por tu trabajo!"
        return render(request, 'salida_exitosa.html', {'mensaje': mensaje, 'hora_salida': asistencia.hora_salida, 'horas_trabajadas': asistencia.horas_trabajadas})

    else:
        return render(request, 'error.html', {'mensaje': 'Tipo de QR no válido.'})

def generar_qr(request, tipo_qr):
    user = request.user
    usuario = Usuario.objects.get(user=user)
    hoy = timezone.localtime(timezone.now()).date()

    if tipo_qr == 'entrada':
        qr_existente = QR.objects.filter(usuario=usuario, qr_entrada_fecha__date=hoy).exists()
        if qr_existente:
            return render(request, 'error.html', {'mensaje': 'Ya has generado un QR de entrada para hoy.'})

        hora_actual = timezone.localtime(timezone.now())  # Asegura que use la hora local
        qr_data = f"Folio prestador {usuario.id}\nEntrada\nGenerado: {hora_actual.strftime('%H:%M:%S')}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qr_obj = QR.objects.create(usuario=usuario, qr_entrada_fecha=hora_actual)

        response = HttpResponse(buffer, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename=QR_Entrada_{usuario.nombre}_{hoy}.png'
        return response

    elif tipo_qr == 'salida':
        qr_existente = QR.objects.filter(usuario=usuario, qr_salida_fecha__date=hoy).exists()
        if qr_existente:
            return render(request, 'error.html', {'mensaje': 'Ya has generado un QR de salida para hoy.'})

        asistencia = Asistencia.objects.filter(usuario=usuario, fecha_escaneo_entrada__date=hoy).first()

        if not asistencia:
            return render(request, 'error.html', {'mensaje': 'No has registrado una entrada hoy.'})

        hora_actual = timezone.localtime(timezone.now())  # Asegura que use la hora local
        qr_data = f"Folio prestador {usuario.id}\nSalida\nHora de escaneo: {hora_actual.strftime('%H:%M:%S')}\nHoras trabajadas: {asistencia.horas_trabajadas:.2f}\nNos vemos mañana, {usuario.nombre}. ¡Gracias por tu trabajo!"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qr_obj = QR.objects.filter(usuario=usuario).latest('qr_entrada_fecha')
        qr_obj.qr_salida_fecha = hora_actual
        qr_obj.save()

        response = HttpResponse(buffer, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename=QR_Salida_{usuario.nombre}_{hoy}.png'
        return response

    return render(request, 'error.html', {'mensaje': 'Tipo de QR no válido.'})


def registrar_asistencia(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_data = data.get('qr_data')

            lines = qr_data.splitlines()
            folio = int(lines[0].split()[-1])
            tipo = lines[1]

            usuario = Usuario.objects.get(id=folio)

            asistencia, created = Asistencia.objects.get_or_create(
                usuario=usuario,
                fecha_escaneo_entrada__date=timezone.now().date()
            )

            if tipo == 'Entrada':
                if not asistencia.fecha_escaneo_entrada:
                    asistencia.fecha_escaneo_entrada = timezone.now()
                    mensaje = "Entrada registrada con éxito."
                else:
                    return JsonResponse({'status': 'error', 'message': 'Ya registraste entrada hoy.'})

            elif tipo == 'Salida':
                if asistencia.fecha_escaneo_entrada and not asistencia.fecha_escaneo_salida:
                    asistencia.fecha_escaneo_salida = timezone.now()
                    asistencia.calcular_horas()
                    mensaje = "Salida registrada con éxito."
                else:
                    return JsonResponse({'status': 'error', 'message': 'Salida no válida.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Tipo de QR no válido.'})

            asistencia.save()
            return JsonResponse({'status': 'success', 'message': mensaje})

        except Usuario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Usuario no encontrado'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})


# ----------------- TABLAS Y VISTAS -----------------
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


# ----------------- LOGIN -----------------
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_active:
                auth_login(request, user)
                return redirect('admin_dashboard' if user.is_superuser else 'inicio')
            else:
                return HttpResponseForbidden("Cuenta desactivada.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def protected_view(request):
    if not request.user.is_active:
        return HttpResponseForbidden("Acceso denegado")
    return render(request, 'protected_template.html', {'message': '¡Bienvenido a la vista protegida!'})


class AdminDashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('login')
        return render(request, 'admin_dashboard.html')


@login_required
def home_view(request):
    return render(request, 'home.html')


# ----------------- FUNCIONES AUXILIARES -----------------
def generate_password(apellido_paterno, apellido_materno, length=10):
    base = (apellido_paterno[:2] + apellido_materno[:2]).lower()
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    extra_length = max(length - len(base), 4)
    random_chars = ''.join(random.choice(chars) for _ in range(extra_length))
    password_list = list(base + random_chars)
    random.shuffle(password_list)
    return ''.join(password_list)


def generate_unique_username(nombre, apellido_paterno, apellido_materno):
    base_username = f"{nombre}{apellido_paterno[:2]}{apellido_materno[:2]}".lower()
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    return username


def enviar_correo_bienvenida(nombre, username, password, correo_electronico):
    subject = "Bienvenido a Control de Asistencias"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [correo_electronico]

    text_content = f"""
    Hola {nombre},

    Tu usuario ha sido creado exitosamente. Aquí están tus credenciales:

    Usuario: {username}
    Contraseña: {password}

    Por favor guarda esta información en un lugar seguro.

    Saludos,
    Equipo de Control de Asistencias
    """

    html_content = f"""
<html>
    <body style="font-family: Arial, sans-serif; background-color: #B08A5B; padding: 20px;">
        <table width="100%" style="max-width: 600px; margin: auto; background: #ffffff; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <tr>
                <td style="text-align: center; padding: 20px; background-color: #602935; border-radius: 8px 8px 0 0;">
                    <img src="https://tuservidor.com/static/img/logo.png" alt="Logo Empresa" width="120" />
                    <h2 style="color: #ffffff; margin-top: 10px;">Control de Asistencias</h2>
                </td>
            </tr>
            <tr>
                <td style="padding: 30px;">
                    <p style="font-size: 16px; color: #602935;">Hola <b>{nombre}</b>,</p>
                    <p style="font-size: 15px; color: #602935;">Nos complace darte la bienvenida al sistema <b>Control de Asistencias</b>. 
                    Tu usuario ha sido creado exitosamente. A continuación te compartimos tus credenciales:</p>

                    <div style="background-color: #ffffff; padding: 15px; border-radius: 6px; margin: 20px 0; font-size: 15px; color: #602935;">
                        <p><b>Usuario:</b> {username}</p>
                        <p><b>Contraseña:</b> {password}</p>
                    </div>

                    <p style="font-size: 14px; color: #602935;">Por favor, guarda esta información en un lugar seguro y cámbiala en tu primer inicio de sesión.</p>
                    
                    <p style="margin-top: 30px; font-size: 15px; color: #602935;">Saludos,<br> 
                    <b>Equipo de Control de Asistencias</b></p>
                </td>
            </tr>
            <tr>
                <td style="text-align: center; padding: 15px; background-color: #B08A5B; border-radius: 0 0 8px 8px; color: #ffffff; font-size: 12px;">
                    © 2025 Control de Asistencias. Todos los derechos reservados.
                </td>
            </tr>
        </table>
    </body>
</html>

    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()




# ----------------- CRUD USUARIOS -----------------
@login_required
def agregar_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            apellido_paterno = form.cleaned_data['apellido_paterno']
            apellido_materno = form.cleaned_data['apellido_materno']
            correo_electronico = form.cleaned_data['correo_electronico']
            password = User.objects.make_random_password()

            username = generate_unique_username(nombre, apellido_paterno, apellido_materno)

            user = User.objects.create_user(username=username, email=correo_electronico, password=password)

            usuario = form.save(commit=False)
            usuario.user = user
            usuario.cambiar_contrasena = True
            usuario.save()

            enviar_correo_bienvenida(usuario.nombre, username, password, correo_electronico)

            messages.success(request, f'Usuario {usuario.nombre} {usuario.apellido_paterno} {usuario.apellido_materno} agregado correctamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioForm()
    return render(request, 'agregar_usuario.html', {'form': form})

# ----------------- REGISTRO DE ENTRADA Y SALIDA -----------------
def entrada_exitosa(request):
    return render(request, 'entrada_exitosa.html')


def salida_exitosa(request):
    return render(request, 'salida_exitosa.html')


@login_required
def lista_usuarios(request):
    usuarios = Usuario.objects.filter(activo=True)
    query = request.GET.get('q')
    if query:
        usuarios = usuarios.filter(nombre__icontains=query)

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


# ----------------- DASHBOARD PRESTADOR -----------------
def inicio_prestador(request):
    return render(request, 'prestador/inicio.html')


@login_required
def dashboard_prestador(request):
    usuario = request.user.usuario
    total_horas_trabajadas = Asistencia.objects.filter(usuario=usuario).aggregate(Sum('horas'))['horas__sum'] or 0
    horas_restantes = usuario.horas_requeridas - usuario.horas_realizadas
    total_asistencias = Asistencia.objects.filter(usuario=usuario).count()
    asistencias_recientes = Asistencia.objects.filter(usuario=usuario).order_by('-fecha_escaneo_entrada')[:5]
    asistencias_por_dia = (
        Asistencia.objects.filter(usuario=usuario)
        .extra({'fecha': "DATE(fecha_escaneo_entrada)"})
        .values('fecha')
        .annotate(total=Count('id'))
        .order_by('fecha')
    )

    context = {
        'usuario': usuario,
        'total_horas_trabajadas': total_horas_trabajadas,
        'horas_restantes': horas_restantes,
        'total_asistencias': total_asistencias,
        'asistencias_recientes': asistencias_recientes,
        'asistencias_por_dia': asistencias_por_dia,
    }

    return render(request, 'prestador/dashboard_prestador.html', context)


@login_required
def reportes_horas(request):
    usuario = get_object_or_404(Usuario, user=request.user)
    asistencias = Asistencia.objects.filter(usuario=usuario).order_by('fecha_escaneo_entrada')
    paginator = Paginator(asistencias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'page_obj': page_obj, 'now': timezone.now()}
    return render(request, 'prestador/reportes.html', context)


@login_required
def descargar_reporte_pdf(request):
    usuario_auth = request.user
    usuario = Usuario.objects.get(user=usuario_auth)
    usuario_nombre_completo = f"{usuario.nombre}_{usuario.apellido_paterno}_{usuario.apellido_materno}".replace(" ", "_")
    asistencias = Asistencia.objects.filter(usuario=usuario).order_by('fecha_escaneo_entrada')

    template = get_template('prestador/reporte_pdf.html')
    html_content = template.render({'asistencias': asistencias, 'now': datetime.now()})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_horas_{usuario_nombre_completo}.pdf"'

    pisa_status = pisa.CreatePDF(src=html_content.encode('utf-8'), dest=response, encoding='utf-8')
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=400)

    return response


# ----------------- DASHBOARD ADMIN -----------------
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard_view(request):
    total_usuarios = Usuario.objects.count()
    usuarios_activos = Usuario.objects.filter(activo=True).count()
    usuarios_inactivos = Usuario.objects.filter(activo=False).count()
    hoy = timezone.now().date()
    asistencias_hoy = Asistencia.objects.filter(fecha_escaneo_entrada__date=hoy)
    total_horas_hoy = asistencias_hoy.aggregate(total_horas=models.Sum('horas'))['total_horas'] or timedelta()
    qrs_totales = QR.objects.count()
    qrs_entrada = QR.objects.filter(qr_salida_fecha__isnull=True).count()
    qrs_salida = QR.objects.filter(qr_salida_fecha__isnull=False).count()
    usuarios = Usuario.objects.all()[:5]
    asistencias = Asistencia.objects.all()[:5]

    context = {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_inactivos': usuarios_inactivos,
        'total_horas_hoy': total_horas_hoy.total_seconds() / 3600,
        'qrs_totales': qrs_totales,
        'qrs_entrada': qrs_entrada,
        'qrs_salida': qrs_salida,
        'usuarios': usuarios,
        'asistencias': asistencias,
    }
    return render(request, 'admin_dashboard.html', context)


def reportes_admin_view(request):
    usuario_id = request.GET.get('usuario')
    fecha = request.GET.get('fecha')
    usuarios = Usuario.objects.all()
    if usuario_id:
        usuarios = usuarios.filter(id=usuario_id)
    asistencias = Asistencia.objects.all()
    if fecha:
        fecha = parse_date(fecha)
        asistencias = asistencias.filter(fecha_escaneo_entrada__date=fecha)
    qrs = QR.objects.all()
    if fecha:
        qrs = qrs.filter(qr_entrada_fecha__date=fecha)
    context = {'usuarios': usuarios, 'asistencias': asistencias, 'qrs': qrs}
    return render(request, 'reportes_admin.html', context)


def reporte_admin_pdf(request):
    usuarios = Usuario.objects.all()
    asistencias = Asistencia.objects.all()
    qrs = QR.objects.all()

    html_string = render_to_string('reportes_admin_pdf.html', {'usuarios': usuarios, 'asistencias': asistencias, 'qrs': qrs})
    result = BytesIO()
    pdf = pisa.CreatePDF(BytesIO(html_string.encode("UTF-8")), dest=result)

    if pdf.err:
        return HttpResponse('Error al generar el PDF', status=500)

    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_admin.pdf"'
    return response
