from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError


from django.db import models
from django.contrib.auth.models import User

class Usuario(models.Model):
    # Campos de información personal
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    telefono = models.CharField(max_length=10)
    correo_electronico = models.EmailField(unique=True)
    fecha_registro = models.DateField(auto_now_add=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    

    # Opciones de servicio
    OPCIONES_SERVICIO = [
        ('SS', 'Servicio Social'),
        ('R', 'Residencias'),
    ]
    tipo_servicio = models.CharField(max_length=2, choices=OPCIONES_SERVICIO)

    # Horas realizadas
    horas_realizadas = models.IntegerField(default=0)
    horas_requeridas = models.IntegerField()
    
    # Nuevo campo para marcar usuario como activo/inactivo
    activo = models.BooleanField(default=True)

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

    def actualizar_horas_realizadas(self):
        total_horas = Asistencia.objects.filter(usuario=self).aggregate(total_horas=models.Sum('horas'))['total_horas']
        if total_horas:
            self.horas_realizadas = int(total_horas.total_seconds() // 3600)
        else:
            self.horas_realizadas = 0
        self.save()



from django.contrib.auth.backends import ModelBackend

class ActiveUserBackend(ModelBackend):
    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and user.usuario.activo

    @property
    def fecha_estimada_conclusion(self):
        dias_necesarios = (self.horas_requeridas - self.horas_realizadas) / 4  # Asumiendo 4 horas por día
        return self.fecha_registro + timedelta(days=dias_necesarios)

    def actualizar_horas_realizadas(self):
        total_horas = Asistencia.objects.filter(usuario=self).aggregate(total_horas=models.Sum('horas'))['total_horas']
        if total_horas:
            self.horas_realizadas = int(total_horas.total_seconds() // 3600)
        else:
            self.horas_realizadas = 0
        self.save()

    


class QR(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    qr_entrada_fecha = models.DateTimeField(auto_now_add=True)
    qr_salida_fecha = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"QR para {self.usuario} generado en {self.qr_entrada_fecha}"
    

class Asistencia(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_escaneo_entrada = models.DateTimeField(blank=True, null=True)
    fecha_escaneo_salida = models.DateTimeField(blank=True, null=True)
    horas = models.DurationField(blank=True, null=True)

    def calcular_horas(self):
        if self.fecha_escaneo_entrada and self.fecha_escaneo_salida:
            diferencia = self.fecha_escaneo_salida - self.fecha_escaneo_entrada
            self.horas = timedelta(seconds=diferencia.total_seconds())
            self.save()
        else:
            self.horas = None

    @property
    def fecha(self):
        return self.fecha_escaneo_entrada.date() if self.fecha_escaneo_entrada else None

    @property
    def hora_entrada(self):
        return self.fecha_escaneo_entrada.strftime('%H:%M') if self.fecha_escaneo_entrada else "-"

    @property
    def hora_salida(self):
        return self.fecha_escaneo_salida.strftime('%H:%M') if self.fecha_escaneo_salida else "-"

    @property
    def horas_trabajadas(self):
        if self.horas:
            return self.horas.total_seconds() / 3600
        return 0.0

    def __str__(self):
        return f"Asistencia de {self.usuario} en {self.fecha_escaneo_entrada}"
