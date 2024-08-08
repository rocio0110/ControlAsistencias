# Generated by Django 3.2.4 on 2024-08-08 02:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('apellido_paterno', models.CharField(max_length=100)),
                ('apellido_materno', models.CharField(max_length=100)),
                ('telefono', models.CharField(max_length=20)),
                ('correo_electronico', models.EmailField(max_length=255)),
                ('tipo_servicio', models.CharField(choices=[('SS', 'Servicio Social'), ('R', 'Residencias')], max_length=2)),
                ('horas_realizadas', models.IntegerField(default=0)),
                ('horas_requeridas', models.IntegerField()),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Asistencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_entrada', models.DateTimeField(blank=True, null=True)),
                ('fecha_salida', models.DateTimeField(blank=True, null=True)),
                ('fecha_scan', models.DateTimeField(default=django.utils.timezone.now)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='asistencia.usuario')),
            ],
        ),
    ]
