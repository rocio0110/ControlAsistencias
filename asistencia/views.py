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

from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Usuario, Asistencia
import json

def registrar_asistencia(request):
    if request.method == 'POST':
        try:
            # Obtener los datos del QR desde la solicitud
            data = json.loads(request.body)
            qr_data = data.get('qr_data')

            # Procesar el texto del QR
            lines = qr_data.splitlines()
            folio = int(lines[0].split()[-1])  # Extraer el folio del prestador
            tipo = lines[1]                     # Extraer el tipo de QR (Entrada o Salida)

            # Buscar al usuario por su ID
            usuario = Usuario.objects.get(id=folio)
            
            # Obtener o crear la asistencia para el día actual
            asistencia, created = Asistencia.objects.get_or_create(
                usuario=usuario, 
                fecha_escaneo_entrada__date=timezone.now().date()
            )
            
            if tipo == 'Entrada':
                if not asistencia.fecha_escaneo_entrada:
                    # Registrar la hora de entrada
                    asistencia.fecha_escaneo_entrada = timezone.now()
                    mensaje = "Entrada registrada con éxito."
                else:
                    return JsonResponse({'status': 'error', 'message': 'Ya se ha registrado una entrada para hoy.'})
            
            elif tipo == 'Salida':
                if asistencia.fecha_escaneo_entrada and not asistencia.fecha_escaneo_salida:
                    # Registrar la hora de salida
                    asistencia.fecha_escaneo_salida = timezone.now()
                    # Calcular las horas trabajadas
                    asistencia.calcular_horas()  # Asegúrate de que esta función calcula la diferencia entre entrada y salida.
                    mensaje = "Salida registrada con éxito."
                else:
                    return JsonResponse({'status': 'error', 'message': 'No se puede registrar salida sin una entrada previa o ya se ha registrado una salida.'})
            
            else:
                return JsonResponse({'status': 'error', 'message': 'Tipo de QR no válido.'})

            # Guardar la asistencia
            asistencia.save()

            return JsonResponse({'status': 'success', 'message': mensaje})
        
        except Usuario.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Usuario no encontrado'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

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



from django.urls import reverse

import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from .models import Usuario, Asistencia

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


from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import QR, Asistencia, Usuario

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

from django.shortcuts import render
from django.db.models import Sum, Count
from .models import Usuario, Asistencia

def dashboard_prestador(request):
    # Obtener el usuario actual
    usuario = request.user.usuario

    # Datos de horas trabajadas
    total_horas_trabajadas = Asistencia.objects.filter(usuario=usuario).aggregate(Sum('horas'))['horas__sum'] or 0
    horas_restantes = usuario.horas_requeridas - usuario.horas_realizadas

    # Número de asistencias registradas
    total_asistencias = Asistencia.objects.filter(usuario=usuario).count()

    # Asistencias recientes (últimos 5 registros)
    asistencias_recientes = Asistencia.objects.filter(usuario=usuario).order_by('-fecha_escaneo_entrada')[:5]

    # Datos para el gráfico de asistencias por día
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
def descargar_reporte_pdf(request):
    # Obtener el usuario autenticado
    usuario_auth = request.user
    # Obtener el objeto Usuario relacionado con el usuario autenticado
    usuario = Usuario.objects.get(user=usuario_auth)
    
    # Construir el nombre completo del usuario
    usuario_nombre_completo = f"{usuario.nombre}_{usuario.apellido_paterno}_{usuario.apellido_materno}".replace(" ", "_")

    # Obtener las asistencias del usuario autenticado
    asistencias = Asistencia.objects.filter(usuario=usuario).order_by('fecha_escaneo_entrada')
    
    # Cargar el template HTML y renderizarlo con los datos
    template = get_template('prestador/reporte_pdf.html')
    html_content = template.render({
        'asistencias': asistencias,
        'now': datetime.now(),  # Utiliza datetime directamente
    })

    # Crear una respuesta HTTP con el tipo de contenido para PDF
    response = HttpResponse(content_type='application/pdf')
    
    # Personalizar el nombre del archivo PDF
    response['Content-Disposition'] = f'attachment; filename="reporte_horas_{usuario_nombre_completo}.pdf"'

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


# views.py
from django.shortcuts import render
from .models import Usuario, QR, Asistencia
from django.db.models import Sum, Count
from django.db import models

@login_required
@user_passes_test(lambda u: u.is_superuser)  # Verificar si el usuario es un superusuario
def admin_dashboard_view(request):

    # Datos del dashboard
    total_usuarios = Usuario.objects.count()
    usuarios_activos = Usuario.objects.filter(activo=True).count()
    usuarios_inactivos = Usuario.objects.filter(activo=False).count()

    # Estadísticas de asistencia
    hoy = timezone.now().date()
    asistencias_hoy = Asistencia.objects.filter(fecha_escaneo_entrada__date=hoy)
    total_horas_hoy = asistencias_hoy.aggregate(total_horas=models.Sum('horas'))['total_horas'] or timedelta()
    
    # Datos de los QR generados
    qrs_totales = QR.objects.count()
    qrs_entrada = QR.objects.filter(qr_salida_fecha__isnull=True).count()
    qrs_salida = QR.objects.filter(qr_salida_fecha__isnull=False).count()

    # Datos adicionales
    usuarios = Usuario.objects.all()[:5]  # Primeros 5 usuarios
    asistencias = Asistencia.objects.all()[:5]  # Primeras 5 asistencias

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

from django.shortcuts import render
from django.db.models import Sum
from .models import Usuario, Asistencia, QR
from django.utils.dateparse import parse_date

def reportes_admin_view(request):
    # Obtener los parámetros de filtro de la solicitud GET
    usuario_id = request.GET.get('usuario')
    fecha = request.GET.get('fecha')

    # Filtrar usuarios
    usuarios = Usuario.objects.all()
    if usuario_id:
        usuarios = usuarios.filter(id=usuario_id)
    
    # Filtrar asistencias
    asistencias = Asistencia.objects.all()
    if fecha:
        fecha = parse_date(fecha)
        asistencias = asistencias.filter(fecha_escaneo_entrada__date=fecha)
    
    # Filtrar QR generados
    qrs = QR.objects.all()
    if fecha:
        qrs = qrs.filter(qr_entrada_fecha__date=fecha)

    context = {
        'usuarios': usuarios,
        'asistencias': asistencias,
        'qrs': qrs,
    }

    return render(request, 'reportes_admin.html', context)



from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO

def reporte_admin_pdf(request):
    # Obtén los datos que necesitas para el reporte
    usuarios = Usuario.objects.all()  # Ajusta esta consulta según tus necesidades
    asistencias = Asistencia.objects.all()  # Ajusta esta consulta según tus necesidades
    qrs = QR.objects.all()  # Ajusta esta consulta según tus necesidades

    # Renderiza la plantilla como un string
    html_string = render_to_string('reportes_admin_pdf.html', {
        'usuarios': usuarios,
        'asistencias': asistencias,
        'qrs': qrs,
    })

    # Crea un archivo PDF a partir del HTML
    result = BytesIO()
    pdf = pisa.CreatePDF(BytesIO(html_string.encode("UTF-8")), dest=result)

    # Verifica si se ha producido algún error
    if pdf.err:
        return HttpResponse('Error al generar el PDF', status=500)

    # Retorna el PDF como una respuesta HTTP
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_admin.pdf"'
    return response
