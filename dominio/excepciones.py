class EcoTechError(Exception):
    """Excepción base de todos los errores propios del sistema."""


class DatoInvalidoError(EcoTechError, ValueError):
    """Un dato no cumple las reglas del negocio (vacío, negativo, formato incorrecto)."""


class RegistroDuplicadoError(EcoTechError):
    """Se intentó guardar un registro que ya existe (id, correo o usuario repetido)."""


class RegistroNoEncontradoError(EcoTechError):
    """No existe el registro buscado."""


class ErrorBaseDatos(EcoTechError):
    """Falla de la base de datos que no corresponde a una regla del negocio."""


class ErrorConexionBD(ErrorBaseDatos):
    """No fue posible abrir la conexión con la base de datos."""


class ErrorAutenticacion(EcoTechError):
    """Falla de inicio de sesión o intento de acceso sin autenticación válida."""


class ErrorServicioExterno(EcoTechError):
    """Error controlado al interactuar con una API externa (sin exponer datos sensibles)."""


class ErrorConexionAPI(ErrorServicioExterno):
    """Error de red o tiempo de espera agotado al contactar un servicio externo."""


class ErrorRespuestaAPI(ErrorServicioExterno):
    """Código HTTP de error o respuesta JSON inválida desde el servicio externo."""
