from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Usuario(models.Model):
    # Campos de información personal
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField(max_length=255)
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    # Opciones de servicio
    OPCIONES_SERVICIO = [
        ('SS', 'Servicio Social'),
        ('R', 'Residencias'),
    ]
    tipo_servicio = models.CharField(max_length=2, choices=OPCIONES_SERVICIO)

    # Horas realizadas
    horas_realizadas = models.IntegerField(default=0)  # Se actualizará según las horas realizadas
    horas_requeridas = models.IntegerField()  # Horas requeridas para el servicio

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"

    def save(self, *args, **kwargs):
        if self.tipo_servicio == 'SS':
            self.horas_requeridas = 480
        elif self.tipo_servicio == 'R':
            self.horas_requeridas = 500
        super().save(*args, **kwargs)

@receiver(post_save, sender=Usuario)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Generar usuario y contraseña basados en nombre y apellidos
        username = instance.nombre.lower()
        password = instance.apellido_paterno[:2].lower() + instance.apellido_materno[:2].lower()

        # Crear usuario en el sistema de autenticación de Django
        user = User.objects.create_user(username=username, password=password)
        instance.user = user
        instance.save()

class Asistencia(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    fecha_entrada = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.usuario.user.username} - {self.fecha_entrada}"

class RegistroEntrada(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    fecha_hora_entrada = models.DateTimeField()

    def __str__(self):
        return f"{self.usuario.user.username} - {self.fecha_hora_entrada}"

# from django.db import models
# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
# from django.utils import timezone

# class UsuarioManager(BaseUserManager):
#     def create_user(self, nombre, apellido_paterno, apellido_materno, correo_electronico, telefono, tipo_usuario):
#         if not correo_electronico:
#             raise ValueError("El usuario debe tener un correo electrónico")
#         if not nombre:
#             raise ValueError("El usuario debe tener un nombre")

#         # Generar nombre de usuario y contraseña
#         nombre_usuario = nombre.lower()
#         contrasena = (apellido_paterno[:2] + apellido_materno[:2]).lower()

#         user = self.model(
#             nombre_usuario=nombre_usuario,
#             correo_electronico=self.normalize_email(correo_electronico),
#             nombre=nombre,
#             apellido_paterno=apellido_paterno,
#             apellido_materno=apellido_materno,
#             telefono=telefono,
#             tipo_usuario=tipo_usuario,
#         )
#         user.set_password(contrasena)
#         user.save(using=self._db)
        
#         # Enviar correo electrónico con las credenciales
#         send_mail(
#             'Credenciales de acceso',
#             f'Nombre de usuario: {nombre_usuario}\nContraseña: {contrasena}',
#             settings.DEFAULT_FROM_EMAIL,
#             [correo_electronico],
#             fail_silently=False,
#         )
        
#         return user

#     def create_superuser(self, nombre_usuario, contrasena, correo_electronico, nombre, apellido_paterno, apellido_materno, telefono):
#         user = self.create_user(
#             nombre_usuario=nombre_usuario,
#             contrasena=contrasena,
#             correo_electronico=correo_electronico,
#             nombre=nombre,
#             apellido_paterno=apellido_paterno,
#             apellido_materno=apellido_materno,
#             telefono=telefono,
#             tipo_usuario='admin'
#         )
#         user.is_admin = True
#         user.save(using=self._db)
#         return user
# class Usuario(AbstractBaseUser):
#     TIPO_USUARIO_CHOICES = [
#         ('admin', 'Admin'),
#         ('servicio_social', 'Servicio Social'),
#         ('residencia', 'Residencia'),
#     ]

#     nombre_usuario = models.CharField(max_length=150, unique=True)
#     correo_electronico = models.EmailField(max_length=254, unique=True)
#     nombre = models.CharField(max_length=30)
#     apellido_paterno = models.CharField(max_length=100)
#     apellido_materno = models.CharField(max_length=100)
#     telefono = models.CharField(max_length=15, blank=True, null=True)
#     tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES)
#     fecha_registro = models.DateTimeField(default=timezone.now)

#     objects = UsuarioManager()

#     REQUIRED_FIELDS = ['correo_electronico', 'nombre', 'apellido_paterno', 'apellido_materno', 'telefono', 'tipo_usuario']
    
#     def save(self, *args, **kwargs):
#         if not self.pk:
#             self.nombre_usuario = self.nombre.lower()
#             self.set_password((self.apellido_paterno[:2] + self.apellido_materno[:2]).lower())
#         super().save(*args, **kwargs)

# class PerfilUsuario(models.Model):
#     TIPO_SERVICIO_CHOICES = [
#         ('servicio_social', 'Servicio Social'),
#         ('residencia', 'Residencia'),
#     ]

#     nombre_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
#     tipo_servicio = models.CharField(max_length=20, choices=TIPO_SERVICIO_CHOICES)
#     telefono = models.CharField(max_length=15, blank=True, null=True)
#     horas_requeridas = models.IntegerField()
#     horas_completadas = models.IntegerField(default=0)

#     def save(self, *args, **kwargs):
#         if self.tipo_servicio == 'servicio_social':
#             self.horas_requeridas = 480
#         elif self.tipo_servicio == 'residencia':
#             self.horas_requeridas = 500
#         super().save(*args, **kwargs)

#     def horas_cubiertas(self):
#         asistencias = self.usuario.asistencia_set.all()  # Uso de 'self.usuario' para obtener las asistencias
#         total_hours = 0
#         for asistencia in asistencias:
#             entrada = asistencia.hora_entrada
#             salida = asistencia.hora_salida
#             if entrada and salida:
#                 duration = (timezone.datetime.combine(timezone.now().date(), salida) - timezone.datetime.combine(timezone.now().date(), entrada)).total_seconds() / 3600
#                 total_hours += duration
#         return total_hours

#     def horas_faltantes(self):
#         return self.horas_requeridas - self.horas_cubiertas()

# class Asistencia(models.Model):
#     usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
#     fecha = models.DateField()
#     hora_entrada = models.TimeField()
#     hora_salida = models.TimeField()
#     codigo_qr = models.CharField(max_length=255)
#     asistencia_confirmada = models.BooleanField(default=False)
#     ultimo_inicio_sesion = models.DateTimeField(null=True)

# class Mensaje(models.Model):
#     ESTADO_CHOICES = [
#         ('leido', 'Leído'),
#         ('no_leido', 'No Leído'),
#     ]

#     remitente = models.ForeignKey(Usuario, related_name='mensajes_enviados', on_delete=models.CASCADE)
#     destinatario = models.ForeignKey(Usuario, related_name='mensajes_recibidos', on_delete=models.CASCADE)
#     fecha_envio = models.DateTimeField(auto_now_add=True)
#     contenido_mensaje = models.TextField()
#     estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='no_leido')

# class Reporte(models.Model):
#     usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
#     fecha_generacion = models.DateTimeField(auto_now_add=True)
#     horas_completadas_periodo = models.IntegerField()
#     horas_faltantes = models.IntegerField()
#     fecha_inicio = models.DateField()
#     fecha_fin = models.DateField()

# class LogActividad(models.Model):
#     usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
#     accion = models.CharField(max_length=255)
#     marca_tiempo = models.DateTimeField(auto_now_add=True)
