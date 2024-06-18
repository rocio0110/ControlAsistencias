from django import forms
from .models import Usuarios  # Asegúrate de importar Usuarios desde .models
import random

# Formulario para agregar usuarios
class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuarios  # Ajusta el modelo a Usuarios
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'tipo_servicio', 'correo_electronico', 'telefono']

    def save(self, commit=True):
        usuario = super().save(commit=False)

        # Generar usuario y contraseña
        usuario.username = f'{usuario.nombre.lower()}.{usuario.apellido_paterno.lower()[:2]}'
        usuario.password = f'{usuario.nombre.lower()}.{usuario.apellido_paterno.lower()[:2]}{random.randint(100, 999)}'
        
        if commit:
            usuario.save()
        
        # Aquí podrías enviar el correo electrónico con las credenciales

        return usuario

# Formulario para el login
class LoginForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
