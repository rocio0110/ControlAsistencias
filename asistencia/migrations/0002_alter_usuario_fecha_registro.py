# Generated by Django 3.2.4 on 2024-07-28 02:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asistencia', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='fecha_registro',
            field=models.DateField(auto_now_add=True),
        ),
    ]