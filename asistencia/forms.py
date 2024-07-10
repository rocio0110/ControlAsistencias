from django import forms
from django.core.mail import send_mail
from django.conf import settings
from .models import Usuarios
import random
import string

# Función para generar contraseñas seguras
def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

# Formulario para agregar usuarios
class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuarios
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'tipo_servicio', 'correo_electronico', 'telefono']

    def save(self, commit=True):
        usuario = super().save(commit=False)

        # Generar usuario y contraseña
        usuario.username = f'{usuario.nombre.lower()}.{usuario.apellido_paterno.lower()[:2]}'
        usuario.password = generate_password()
        
        if commit:
            usuario.save()

            # Enviar correo electrónico con las credenciales
            send_mail(
                'Tus credenciales de acceso',
                f'Hola {usuario.nombre},\n\nTu usuario es: {usuario.username}\nTu contraseña es: {usuario.password}\n\nPor favor, cambia tu contraseña después de iniciar sesión.',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.correo_electronico],
                fail_silently=False,
            )

        return usuario

    # Validación para asegurar que el correo electrónico es único
    def clean_correo_electronico(self):
        correo_electronico = self.cleaned_data.get('correo_electronico')
        if Usuarios.objects.filter(correo_electronico=correo_electronico).exists():
            raise forms.ValidationError('El correo electrónico ya está en uso.')
        return correo_electronico

# Formulario para el login
class LoginForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
