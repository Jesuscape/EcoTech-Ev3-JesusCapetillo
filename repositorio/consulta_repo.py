import json
from pathlib import Path

from dominio.excepciones import ErrorBaseDatos
from repositorio.base_repo import BaseRepositorio
from repositorio.conexion import RAIZ


class ConsultaExternaRepositorio(BaseRepositorio):
    """Persistencia local parametrizada de consultas de clima y pagos internacionales."""

    def guardar_clima(self, registro):
        self._ejecutar(
            "INSERT INTO consulta_clima "
            "(proyecto, ciudad, pais, temperatura_c, humedad_pct, estado_clima, "
            "recomendacion, usuario_consulta, fecha_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                registro["proyecto"],
                registro["ciudad"],
                registro["pais"],
                registro["temperatura_c"],
                registro["humedad_pct"],
                registro["estado_clima"],
                registro["recomendacion"],
                registro["usuario_consulta"],
                registro["fecha_utc"],
            ),
        )

    def listar_climas(self, limite=10):
        filas = self._consultar(
            "SELECT id_consulta, proyecto, ciudad, pais, temperatura_c, humedad_pct, "
            "estado_clima, recomendacion, usuario_consulta, fecha_utc "
            "FROM consulta_clima ORDER BY id_consulta DESC LIMIT ?",
            (limite,),
        )
        return [
            {
                "id_consulta": f[0],
                "proyecto": f[1],
                "ciudad": f[2],
                "pais": f[3],
                "temperatura_c": f[4],
                "humedad_pct": f[5],
                "estado_clima": f[6],
                "recomendacion": f[7],
                "usuario_consulta": f[8],
                "fecha_utc": f[9],
            }
            for f in filas
        ]

    def guardar_pago(self, registro):
        self._ejecutar(
            "INSERT INTO pago_internacional "
            "(id_persona, proyecto, moneda_origen, moneda_destino, monto_origen, "
            "tasa_cambio, monto_convertido, usuario_registro, fecha_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                registro.get("id_persona"),
                registro["proyecto"],
                registro["moneda_origen"],
                registro["moneda_destino"],
                registro["monto_origen"],
                registro["tasa_cambio"],
                registro["monto_convertido"],
                registro["usuario_registro"],
                registro["fecha_utc"],
            ),
        )

    def listar_pagos(self, limite=10):
        filas = self._consultar(
            "SELECT id_pago, id_persona, proyecto, moneda_origen, moneda_destino, "
            "monto_origen, tasa_cambio, monto_convertido, usuario_registro, fecha_utc "
            "FROM pago_internacional ORDER BY id_pago DESC LIMIT ?",
            (limite,),
        )
        return [
            {
                "id_pago": f[0],
                "id_persona": f[1],
                "proyecto": f[2],
                "moneda_origen": f[3],
                "moneda_destino": f[4],
                "monto_origen": f[5],
                "tasa_cambio": f[6],
                "monto_convertido": f[7],
                "usuario_registro": f[8],
                "fecha_utc": f[9],
            }
            for f in filas
        ]

    def exportar_historial_json(self, ruta_destino=None):
        """Exporta el historial de consultas externas a un archivo JSON local."""
        destino = Path(ruta_destino) if ruta_destino else RAIZ / "datos" / "historial_servicios.json"
        resumen = {
            "consultas_clima": self.listar_climas(limite=100),
            "pagos_internacionales": self.listar_pagos(limite=100),
        }
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(
                json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            return destino
        except OSError as error:
            raise ErrorBaseDatos("No fue posible exportar el respaldo JSON local.") from error
