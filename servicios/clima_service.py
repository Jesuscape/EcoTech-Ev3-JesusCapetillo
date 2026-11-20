"""Servicio de consulta climática externa (Open-Meteo) para planificación operativa."""
from datetime import datetime, timezone
import os

from dominio.excepciones import ErrorRespuestaAPI
from dominio.validaciones import ciudad_valida, proyecto_valido
from repositorio.conexion import cargar_env


class ServicioClima:
    """Obtiene temperatura, humedad y estado del tiempo desde Open-Meteo y los persiste."""

    URL_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
    URL_PRONOSTICO = "https://api.open-meteo.com/v1/forecast"

    CODIGOS_WMO = {
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

    CODIGOS_ADVERSOS = {55, 63, 65, 73, 75, 81, 82, 95, 96, 99}

    def __init__(self, cliente_http, repo_consultas=None):
        cargar_env()
        self._http = cliente_http
        self._repo = repo_consultas
        # Lectura segura de clave opcional desde variable de entorno (nunca hardcodeada)
        self.__api_key = os.environ.get("ECOTECH_CLIMA_API_KEY", "").strip()

    def _encabezados(self):
        return {"X-API-Key": self.__api_key} if self.__api_key else None

    def consultar_clima(self, proyecto, ciudad, usuario):
        proyecto_limpio = proyecto_valido(proyecto)
        ciudad_limpia = ciudad_valida(ciudad)

        geo = self._http.obtener_json(
            self.URL_GEOCODING,
            parametros={"name": ciudad_limpia, "count": 1, "language": "es", "format": "json"},
            encabezados=self._encabezados(),
        )
        resultados = geo.get("results")
        if not resultados or not isinstance(resultados, list):
            raise ErrorRespuestaAPI(f"No se encontró información geográfica para la ciudad '{ciudad_limpia}'.")

        ubicacion = resultados[0]
        latitud = ubicacion.get("latitude")
        longitud = ubicacion.get("longitude")
        if latitud is None or longitud is None:
            raise ErrorRespuestaAPI("La API entregó coordenadas incompletas.")

        clima = self._http.obtener_json(
            self.URL_PRONOSTICO,
            parametros={
                "latitude": latitud,
                "longitude": longitud,
                "current": "temperature_2m,relative_humidity_2m,weather_code",
            },
            encabezados=self._encabezados(),
        )
        actual = clima.get("current", {})
        temperatura = actual.get("temperature_2m")
        humedad = actual.get("relative_humidity_2m")
        codigo = actual.get("weather_code")
        if temperatura is None or humedad is None or codigo is None:
            raise ErrorRespuestaAPI("La API de clima devolvió datos incompletos.")

        estado = self.CODIGOS_WMO.get(codigo, "Condición climática variable")
        es_adverso = codigo in self.CODIGOS_ADVERSOS or float(temperatura) < 0 or float(temperatura) > 38
        recomendacion = (
            "ALERTA OPERATIVA: Evaluar reprogramación de actividades en terreno."
            if es_adverso
            else "CONDICIONES FAVORABLES: Apto para ejecución de actividades en terreno."
        )

        registro = {
            "proyecto": proyecto_limpio,
            "ciudad": ubicacion.get("name", ciudad_limpia),
            "pais": ubicacion.get("country", "Desconocido"),
            "temperatura_c": round(float(temperatura), 1),
            "humedad_pct": int(humedad),
            "estado_clima": estado,
            "recomendacion": recomendacion,
            "usuario_consulta": usuario,
            "fecha_utc": datetime.now(timezone.utc).isoformat(),
        }

        if self._repo is not None:
            self._repo.guardar_clima(registro)
        return registro
