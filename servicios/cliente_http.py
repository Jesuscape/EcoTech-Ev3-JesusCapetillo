"""Cliente HTTP seguro basado en la librería oficial requests.
Centraliza timeout, verificación TLS, validación de códigos HTTP y sanitización de errores."""
import os
import requests

from dominio.excepciones import ErrorConexionAPI, ErrorRespuestaAPI
from repositorio.conexion import cargar_env


class ClienteHTTP:
    """Encapsula solicitudes GET a servicios externos sin exponer detalles internos en errores."""

    def __init__(self, timeout=None):
        cargar_env()
        self.__timeout = self._resolver_timeout(timeout)
        self.__sesion = requests.Session()
        self.__sesion.headers.update({"User-Agent": "EcoTechSolutions-ES3/1.0"})

    @staticmethod
    def _resolver_timeout(timeout):
        if timeout is not None:
            return timeout if 1 <= timeout <= 30 else 10
        try:
            valor = int(os.environ.get("ECOTECH_API_TIMEOUT", "10"))
            return valor if 1 <= valor <= 30 else 10
        except ValueError:
            return 10

    @property
    def timeout(self):
        return self.__timeout

    @staticmethod
    def validar_estado_http(status_code):
        """Traduce códigos HTTP en excepciones de negocio con mensajes seguros."""
        if status_code == 200:
            return
        if status_code == 400:
            raise ErrorRespuestaAPI("La solicitud fue rechazada por datos inválidos (HTTP 400).")
        if status_code in (401, 403):
            raise ErrorRespuestaAPI(
                "Error de autorización con el servicio externo. Revise la configuración."
            )
        if status_code == 404:
            raise ErrorRespuestaAPI("El recurso solicitado no fue encontrado en el servicio externo (HTTP 404).")
        if status_code == 429:
            raise ErrorRespuestaAPI(
                "Se superó el límite de consultas del servicio externo (HTTP 429). Intente más tarde."
            )
        if status_code >= 500:
            raise ErrorRespuestaAPI(
                "El servicio externo presenta una falla temporal (HTTP 5xx). Intente nuevamente."
            )
        raise ErrorRespuestaAPI(f"Respuesta inesperada del servicio externo (HTTP {status_code}).")

    def obtener_json(self, url, parametros=None, encabezados=None):
        """Realiza una solicitud GET HTTPS segura y retorna el JSON validado."""
        try:
            respuesta = self.__sesion.get(
                url,
                params=parametros,
                headers=encabezados,
                timeout=self.__timeout,
                verify=True,
            )
            self.validar_estado_http(respuesta.status_code)
            datos = respuesta.json()
            if not isinstance(datos, dict):
                raise ErrorRespuestaAPI("La respuesta del servicio externo no tiene formato JSON válido.")
            return datos
        except requests.exceptions.Timeout:
            raise ErrorConexionAPI(
                "Tiempo de espera agotado al conectar con el servicio externo."
            ) from None
        except requests.exceptions.ConnectionError:
            raise ErrorConexionAPI(
                "No fue posible conectar con el servicio externo. Verifique su conexión a internet."
            ) from None
        except requests.exceptions.RequestException:
            raise ErrorConexionAPI(
                "Ocurrió un problema de comunicación con el servicio externo."
            ) from None
        except ValueError:
            raise ErrorRespuestaAPI(
                "No fue posible interpretar los datos JSON entregados por el servicio externo."
            ) from None

    def cerrar(self):
        self.__sesion.close()
