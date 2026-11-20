"""Validaciones compartidas por todas las clases del dominio y servicios externos."""
from datetime import date
import re

from dominio.excepciones import DatoInvalidoError

_PATRON_USUARIO = re.compile(r"^[a-zA-Z0-9_.-]{4,25}$")
_PATRON_CIUDAD = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']{2,60}$")
_PATRON_MONEDA = re.compile(r"^[A-Z]{3}$")
_PATRON_PROYECTO = re.compile(r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-_.,]{3,80}$")


def texto_no_vacio(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        raise DatoInvalidoError(f"{campo} no puede estar vacío.")
    return valor.strip()


def entero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise DatoInvalidoError(f"{campo} debe ser un número entero mayor a 0.")
    return valor


def numero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
        raise DatoInvalidoError(f"{campo} debe ser un número mayor a 0.")
    return float(valor)


def correo_valido(valor):
    valor = texto_no_vacio(valor, "El correo")
    usuario, _, dominio = valor.partition("@")
    if not usuario or "." not in dominio:
        raise DatoInvalidoError("El correo no tiene un formato válido (ej: nombre@dominio.cl).")
    return valor


def fecha_valida(valor, campo):
    if not isinstance(valor, date):
        raise DatoInvalidoError(f"{campo} debe ser una fecha.")
    return valor


def usuario_valido(valor):
    valor = texto_no_vacio(valor, "El nombre de usuario")
    if not _PATRON_USUARIO.match(valor):
        raise DatoInvalidoError(
            "El nombre de usuario debe tener entre 4 y 25 caracteres (letras, números, '.', '_' o '-')."
        )
    return valor


def clave_segura_valida(valor):
    valor = texto_no_vacio(valor, "La clave")
    if len(valor) < 8 or len(valor) > 64:
        raise DatoInvalidoError("La clave debe tener entre 8 y 64 caracteres.")
    if not any(c.isupper() for c in valor) or not any(c.isdigit() for c in valor):
        raise DatoInvalidoError(
            "La clave debe incluir al menos una letra mayúscula y un número."
        )
    return valor


def ciudad_valida(valor):
    valor = texto_no_vacio(valor, "La ciudad")
    if not _PATRON_CIUDAD.match(valor):
        raise DatoInvalidoError(
            "Nombre de ciudad inválido. Use solo letras, espacios o guiones (2 a 60 caracteres)."
        )
    return valor


def codigo_moneda_valido(valor, campo="El código de moneda"):
    valor = texto_no_vacio(valor, campo).upper()
    if not _PATRON_MONEDA.match(valor):
        raise DatoInvalidoError(
            f"{campo} debe ser un código ISO de 3 letras (ej: CLP, USD, EUR, BRL)."
        )
    return valor


def proyecto_valido(valor):
    valor = texto_no_vacio(valor, "El nombre del proyecto")
    if not _PATRON_PROYECTO.match(valor):
        raise DatoInvalidoError(
            "Nombre de proyecto inválido (3 a 80 caracteres alfanuméricos)."
        )
    return valor
