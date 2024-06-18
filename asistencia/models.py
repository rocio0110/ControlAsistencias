# Importaciones necesarias
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
# Función para crear automáticamente un usuario de Django después de guardar un Usuario
from django.db.models.signals import post_save
from django.dispatch import receiver


# Modelo para la información personal de Usuarios
class Usuarios(models.Model):
    # Campos de información personal
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField(max_length=255)

    # Opciones de servicio
    OPCIONES_SERVICIO = [
        ('SS', 'Servicio Social'),
        ('R', 'Residencias'),
    ]
    tipo_servicio = models.CharField(max_length=2, choices=OPCIONES_SERVICIO)

    # Horas realizadas
    horas_realizadas = models.IntegerField(default=0)  # Se actualizará según las horas realizadas

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"

@receiver(post_save, sender=Usuarios)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Generar usuario y contraseña basados en nombre y apellidos
        username = instance.nombre.lower()
        password = instance.apellido_paterno[:2].lower() + instance.apellido_materno[:2].lower()

        # Crear usuario en el sistema de autenticación de Django
        user = User.objects.create_user(username=username, password=password)
        instance.user = user
        instance.save()

# Modelos de Asistencia y RegistroEntrada
class Asistencia(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha_entrada = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha_entrada}"

class RegistroEntrada(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha_hora_entrada = models.DateTimeField()

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha_hora_entrada}"

