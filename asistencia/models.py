from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models
from datetime import timedelta


class Usuario(models.Model):
    # Campos de información personal
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField(max_length=255)
    # fecha_registro = models.DateField(auto_now_add=True)

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

    @property
    def fecha_estimada_conclusion(self):
        dias_necesarios = (self.horas_requeridas - self.horas_realizadas) / 4  # Asumiendo 4 horas por día
        return self.fecha_registro + timedelta(days=dias_necesarios)



class Asistencia(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    fecha_entrada = models.DateTimeField(null=True, blank=True)
    fecha_salida = models.DateTimeField(null=True, blank=True)
    fecha_scan = models.DateTimeField(default=timezone.now)  # Asegúrate de importar timezone correctamente

    def clean(self):
        if self.fecha_salida and self.fecha_entrada and self.fecha_salida < self.fecha_entrada:
            raise ValidationError('La fecha de salida no puede ser anterior a la fecha de entrada.')
        if self.fecha_entrada and Asistencia.objects.filter(usuario=self.usuario, fecha_entrada__date=self.fecha_entrada.date()).exclude(id=self.id).exists():
            raise ValidationError('Ya se ha registrado una entrada para este usuario en el día de hoy.')
        if self.fecha_salida and Asistencia.objects.filter(usuario=self.usuario, fecha_salida__date=self.fecha_salida.date()).exclude(id=self.id).exists():
            raise ValidationError('Ya se ha registrado una salida para este usuario en el día de hoy.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.user.username} - {self.fecha_entrada}"
