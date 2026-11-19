from datetime import datetime, timezone
from typing import Any
import requests
from src.config import Config


class APIServiceError(Exception):
    """Excepción controlada con mensajes seguros para mostrar al usuario."""


class BaseAPIClient:
    """Cliente base HTTP con manejo centralizado de errores y códigos de estado."""

    def __init__(self) -> None:
        self.timeout = Config.get_timeout()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "EcoTechSolutions-Client/1.0"})

    def _handle_http_status(self, response: requests.Response) -> None:
        status = response.status_code
        if status == 200:
            return
        if status == 400:
            raise APIServiceError("Solicitud inválida. Revise los datos ingresados.")
        if status in (401, 403):
            raise APIServiceError(
                "Error de autorización con el servicio externo. Verifique la configuración."
            )
        if status == 404:
            raise APIServiceError(
                "No se encontró información para el recurso solicitado."
            )
        if status == 429:
            raise APIServiceError(
                "Límite de consultas excedido en el servicio externo. Intente más tarde."
            )
        if status >= 500:
            raise APIServiceError(
                "El servicio externo presenta fallas temporales. Intente nuevamente más tarde."
            )
        raise APIServiceError(
            f"El servicio externo respondió con un estado inesperado (HTTP {status})."
        )

    def _get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout, verify=True
            )
            self._handle_http_status(response)
            data = response.json()
            if not isinstance(data, dict):
                raise APIServiceError(
                    "Formato de respuesta no válido desde el servicio externo."
                )
            return data
        except requests.exceptions.Timeout:
            raise APIServiceError(
                "Tiempo de espera agotado al conectar con el servicio externo."
            ) from None
        except requests.exceptions.ConnectionError:
            raise APIServiceError(
                "No se pudo establecer conexión con el servicio externo. Revise su red."
            ) from None
        except requests.exceptions.RequestException:
            raise APIServiceError(
                "Ocurrió un error de comunicación con el servicio externo."
            ) from None
        except ValueError:
            raise APIServiceError(
                "No fue posible interpretar la respuesta JSON del servicio externo."
            ) from None


class WeatherService(BaseAPIClient):
    """Consume datos climáticos externos para la planificación operativa de proyectos."""

    WMO_DESCRIPTIONS = {
        0: "Cielo despejado",
        1: "Mayormente despejado",
        2: "Parcialmente nublado",
        3: "Nublado",
        45: "Niebla",
        48: "Niebla con escarcha",
        51: "Llovizna ligera",
        53: "Llovizna moderada",
        55: "Llovizna intensa",
        61: "Lluvia ligera",
        63: "Lluvia moderada",
        65: "Lluvia intensa",
        71: "Nieve ligera",
        73: "Nieve moderada",
        75: "Nieve intensa",
        80: "Chubascos ligeros",
        81: "Chubascos moderados",
        82: "Chubascos fuertes",
        95: "Tormenta eléctrica",
        96: "Tormenta eléctrica con granizo",
        99: "Tormenta eléctrica severa",
    }

    def get_weather_by_city(self, city: str) -> dict[str, Any]:
        geo_data = self._get_json(
            Config.GEOCODING_API_URL,
            params={"name": city, "count": 1, "language": "es", "format": "json"},
        )

        results = geo_data.get("results")
        if not results or not isinstance(results, list):
            raise APIServiceError(f"No se encontró la ciudad '{city}'.")

        location = results[0]
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        if latitude is None or longitude is None:
            raise APIServiceError("Datos geográficos incompletos recibidos de la API.")

        weather_data = self._get_json(
            Config.WEATHER_API_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,weather_code",
            },
        )

        current = weather_data.get("current", {})
        temperature = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        code = current.get("weather_code")

        if temperature is None or humidity is None or code is None:
            raise APIServiceError("La API de clima devolvió datos incompletos.")

        condition = self.WMO_DESCRIPTIONS.get(code, "Condición climática variable")
        adverse_codes = {55, 63, 65, 73, 75, 81, 82, 95, 96, 99}
        recommendation = (
            "ALERTA OPERATIVA: Evaluar reprogramación de trabajos en terreno."
            if code in adverse_codes or temperature < 0 or temperature > 38
            else "CONDICIONES FAVORABLES: Apto para ejecución de actividades en terreno."
        )

        return {
            "ciudad": location.get("name", city),
            "pais": location.get("country", "Desconocido"),
            "temperatura_c": float(temperature),
            "humedad_pct": int(humidity),
            "estado_clima": condition,
            "recomendacion_operativa": recommendation,
            "fecha_consulta_utc": datetime.now(timezone.utc).isoformat(),
        }


class CurrencyService(BaseAPIClient):
    """Consume indicadores de tipo de cambio para pagos internacionales."""

    def convert_payment(
        self, base_currency: str, target_currency: str, amount: float
    ) -> dict[str, Any]:
        url = f"{Config.CURRENCY_API_URL}/{base_currency}"
        data = self._get_json(url)

        if data.get("result") != "success":
            raise APIServiceError(
                f"No fue posible obtener tasas de cambio para '{base_currency}'."
            )

        rates = data.get("rates", {})
        if target_currency not in rates:
            raise APIServiceError(
                f"La moneda de destino '{target_currency}' no está disponible."
            )

        rate = rates[target_currency]
        if not isinstance(rate, (int, float)) or rate <= 0:
            raise APIServiceError("La tasa de cambio recibida no es válida.")

        converted_amount = round(amount * rate, 2)

        return {
            "moneda_origen": base_currency,
            "moneda_destino": target_currency,
            "monto_origen": amount,
            "tasa_cambio": round(float(rate), 6),
            "monto_convertido": converted_amount,
            "actualizacion_api": data.get("time_last_update_utc", "No informada"),
            "fecha_consulta_utc": datetime.now(timezone.utc).isoformat(),
        }
