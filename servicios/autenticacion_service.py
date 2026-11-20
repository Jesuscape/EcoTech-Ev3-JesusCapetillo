"""Servicio de autenticación y control de sesión usando Credencial y GestorCifrado (PBKDF2)."""
import os

from dominio.excepciones import ErrorAutenticacion, RegistroNoEncontradoError
from repositorio.conexion import cargar_env


class ServicioAutenticacion:
    """Controla el acceso al sistema mediante credenciales encriptadas y límite de intentos."""

    _ERROR_GENERICO = "Credenciales inválidas. Verifique usuario y contraseña."

    def __init__(self, repo_empleado):
        cargar_env()
        self._repo_emp = repo_empleado
        self.__credencial_activa = None
        self.__intentos_fallidos = 0
        self.__max_intentos = self._resolver_max_intentos()

    @staticmethod
    def _resolver_max_intentos():
        try:
            valor = int(os.environ.get("ECOTECH_MAX_INTENTOS_LOGIN", "3"))
            return valor if 1 <= valor <= 5 else 3
        except ValueError:
            return 3

    @property
    def max_intentos(self):
        return self.__max_intentos

    @property
    def intentos_restantes(self):
        return max(0, self.__max_intentos - self.__intentos_fallidos)

    @property
    def usuario_actual(self):
        return self.__credencial_activa.nombreUsuario if self.__credencial_activa else None

    @property
    def perfil_actual(self):
        return self.__credencial_activa.perfil.etiqueta if self.__credencial_activa else None

    def esta_autenticado(self):
        return self.__credencial_activa is not None

    def requerir_autenticacion(self):
        if not self.esta_autenticado():
            raise ErrorAutenticacion("Acceso denegado: debe iniciar sesión para usar esta funcionalidad.")

    def hay_usuarios_registrados(self):
        return self._repo_emp.contar_credenciales() > 0

    def iniciar_sesion(self, nombre_usuario, clave):
        if self.__intentos_fallidos >= self.__max_intentos:
            raise ErrorAutenticacion("Acceso bloqueado temporalmente por exceso de intentos fallidos.")

        usuario = nombre_usuario.strip() if isinstance(nombre_usuario, str) else ""
        if not usuario or not isinstance(clave, str) or not clave:
            self.__intentos_fallidos += 1
            raise ErrorAutenticacion("Debe ingresar usuario y contraseña válidos.")

        try:
            credencial = self._repo_emp.obtener_credencial(usuario)
        except RegistroNoEncontradoError:
            self.__intentos_fallidos += 1
            raise ErrorAutenticacion(self._ERROR_GENERICO) from None

        if not credencial.validarAcceso(clave):
            self.__intentos_fallidos += 1
            raise ErrorAutenticacion(self._ERROR_GENERICO)

        self.__credencial_activa = credencial
        self.__intentos_fallidos = 0
        return credencial

    def cerrar_sesion(self):
        self.__credencial_activa = None
        self.__intentos_fallidos = 0
