
from django import forms
from django.core.mail import send_mail
from django.conf import settings
from .models import Usuario
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
        model = Usuario
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'telefono','tipo_servicio', 'correo_electronico']

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
        if Usuario.objects.filter(correo_electronico=correo_electronico).exists():
            raise forms.ValidationError('El correo electrónico ya está en uso.')
        return correo_electronico

# Formulario para el login
class LoginForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)


# from django import forms
# from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from .models import Usuario, PerfilUsuario, Asistencia, Mensaje, Reporte

# class CustomAuthenticationForm(AuthenticationForm):
#     username = forms.CharField(
#         label='Nombre de Usuario',
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de Usuario'})
#     )
#     password = forms.CharField(
#         label='Contraseña',
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
#     )


# class UsuarioForm(UserCreationForm):
#     class Meta:
#         model = Usuario
#         fields = ['correo_electronico', 'nombre', 'apellido_paterno', 'apellido_materno', 'telefono', 'tipo_usuario']

# class PerfilUsuarioForm(forms.ModelForm):
#     class Meta:
#         model = PerfilUsuario
#         fields = ['nombre_usuario', 'tipo_servicio', 'horas_completadas']  # Eliminado 'horas_requeridas' porque se gestiona en el modelo

# class AsistenciaForm(forms.ModelForm):
#     class Meta:
#         model = Asistencia
#         fields = ['usuario', 'fecha', 'hora_entrada', 'hora_salida', 'codigo_qr', 'asistencia_confirmada']

# class MensajeForm(forms.ModelForm):
#     class Meta:
#         model = Mensaje
#         fields = ['remitente', 'destinatario', 'contenido_mensaje', 'estado']

# class ReporteForm(forms.ModelForm):
#     class Meta:
#         model = Reporte
#         fields = ['usuario', 'horas_completadas_periodo', 'horas_faltantes', 'fecha_inicio', 'fecha_fin']
