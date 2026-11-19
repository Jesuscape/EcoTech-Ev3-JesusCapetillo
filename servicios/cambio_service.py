"""Servicio de indicadores económicos y tipo de cambio (ExchangeRate-API) para pagos internacionales."""
from datetime import datetime, timezone
import os

from dominio.excepciones import ErrorRespuestaAPI
from dominio.validaciones import codigo_moneda_valido, numero_positivo, proyecto_valido
from repositorio.conexion import cargar_env


class ServicioCambio:
    """Consulta tipos de cambio actualizados y calcula pagos internacionales ajustados."""

    URL_BASE = "https://open.er-api.com/v6/latest"

    def __init__(self, cliente_http, repo_consultas=None):
        cargar_env()
        self._http = cliente_http
        self._repo = repo_consultas
        # Lectura segura de clave opcional desde variable de entorno (nunca hardcodeada)
        self.__api_key = os.environ.get("ECOTECH_CAMBIO_API_KEY", "").strip()

    def _encabezados(self):
        return {"Authorization": f"Bearer {self.__api_key}"} if self.__api_key else None

    def calcular_pago_internacional(
        self, proyecto, moneda_origen, moneda_destino, monto, usuario, id_persona=None
    ):
        proyecto_limpio = proyecto_valido(proyecto)
        origen = codigo_moneda_valido(moneda_origen, "La moneda de origen")
        destino = codigo_moneda_valido(moneda_destino, "La moneda de destino")
        monto_valido = numero_positivo(monto, "El monto a pagar")

        datos = self._http.obtener_json(
            f"{self.URL_BASE}/{origen}", encabezados=self._encabezados()
        )
        if datos.get("result") != "success":
            raise ErrorRespuestaAPI(f"No fue posible obtener tasas de cambio para '{origen}'.")

        tasas = datos.get("rates", {})
        if not isinstance(tasas, dict) or destino not in tasas:
            raise ErrorRespuestaAPI(f"La moneda de destino '{destino}' no está disponible en la API.")

        tasa = tasas[destino]
        if not isinstance(tasa, (int, float)) or tasa <= 0:
            raise ErrorRespuestaAPI("La tasa de cambio recibida desde la API no es válida.")

        convertido = round(monto_valido * float(tasa), 2)
        registro = {
            "id_persona": id_persona,
            "proyecto": proyecto_limpio,
            "moneda_origen": origen,
            "moneda_destino": destino,
            "monto_origen": round(monto_valido, 2),
            "tasa_cambio": round(float(tasa), 6),
            "monto_convertido": convertido,
            "actualizacion_api": datos.get("time_last_update_utc", "No informada"),
            "usuario_registro": usuario,
            "fecha_utc": datetime.now(timezone.utc).isoformat(),
        }

        if self._repo is not None:
            self._repo.guardar_pago(registro)
        return registro
