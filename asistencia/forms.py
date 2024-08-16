from django import forms
from .models import Usuario
import random
import string

def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'telefono', 'correo_electronico', 'tipo_servicio']
        error_messages = {
            'nombre': {
                'required': 'Todos los campos son obligatorios.',
            },
            'apellido_paterno': {
                'required': 'Todos los campos son obligatorios.',
            },
            'apellido_materno': {
                'required': 'Todos los campos son obligatorios.',
            },
            'telefono': {
                'required': 'Todos los campos son obligatorios.',
                'max_length': 'El teléfono debe tener exactamente 10 dígitos.',
            },
            'correo_electronico': {
                'required': 'Todos los campos son obligatorios.',
                'invalid': 'Ingresa un correo electrónico válido.',
            },
            'tipo_servicio': {
                'required': 'Todos los campos son obligatorios.',
            },
        }

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if len(telefono) != 10:
            raise forms.ValidationError('El teléfono debe tener exactamente 10 dígitos.')
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre')
        apellido_paterno = cleaned_data.get('apellido_paterno')
        apellido_materno = cleaned_data.get('apellido_materno')

        if Usuario.objects.filter(nombre=nombre, apellido_paterno=apellido_paterno, apellido_materno=apellido_materno).exists():
            raise forms.ValidationError('Ya existe un usuario con el mismo nombre y apellidos.')

        return cleaned_data

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
