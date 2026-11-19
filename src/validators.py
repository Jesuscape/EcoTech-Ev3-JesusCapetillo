import re


class InputValidator:
    """Valida y sanitiza todas las entradas del usuario antes de procesarlas."""

    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{4,25}$")
    CITY_PATTERN = re.compile(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']{2,60}$")
    CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
    PROJECT_PATTERN = re.compile(r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-_]{3,60}$")

    @classmethod
    def validate_username(cls, username: str) -> tuple[bool, str]:
        cleaned = username.strip()
        if not cleaned:
            return False, "El nombre de usuario no puede estar vacío."
        if not cls.USERNAME_PATTERN.match(cleaned):
            return (
                False,
                "El usuario debe tener entre 4 y 25 caracteres (letras, números, '.', '_' o '-').",
            )
        return True, cleaned

    @classmethod
    def validate_password(cls, password: str) -> tuple[bool, str]:
        if not password or not password.strip():
            return False, "La contraseña no puede estar vacía."
        if len(password) < 8 or len(password) > 64:
            return False, "La contraseña debe tener entre 8 y 64 caracteres."
        if not any(c.isupper() for c in password):
            return False, "La contraseña debe incluir al menos una letra mayúscula."
        if not any(c.isdigit() for c in password):
            return False, "La contraseña debe incluir al menos un número."
        return True, password

    @classmethod
    def validate_city(cls, city: str) -> tuple[bool, str]:
        cleaned = city.strip()
        if not cleaned:
            return False, "El nombre de la ciudad no puede estar vacío."
        if not cls.CITY_PATTERN.match(cleaned):
            return (
                False,
                "Ciudad inválida. Use solo letras, espacios o guiones (2 a 60 caracteres).",
            )
        return True, cleaned

    @classmethod
    def validate_currency_code(cls, code: str) -> tuple[bool, str]:
        cleaned = code.strip().upper()
        if not cls.CURRENCY_PATTERN.match(cleaned):
            return (
                False,
                "Código de moneda inválido. Debe ser un código ISO de 3 letras (ej: USD, CLP, EUR).",
            )
        return True, cleaned

    @classmethod
    def validate_amount(cls, raw_amount: str) -> tuple[bool, float | str]:
        cleaned = raw_amount.strip().replace(",", ".")
        if not cleaned:
            return False, "El monto no puede estar vacío."
        try:
            amount = float(cleaned)
        except ValueError:
            return False, "Debe ingresar un monto numérico válido."
        if amount <= 0 or amount > 1_000_000_000:
            return False, "El monto debe ser mayor a 0 y menor a 1.000.000.000."
        return True, round(amount, 2)

    @classmethod
    def validate_project_name(cls, name: str) -> tuple[bool, str]:
        cleaned = name.strip()
        if not cls.PROJECT_PATTERN.match(cleaned):
            return (
                False,
                "Nombre de proyecto inválido (3 a 60 caracteres alfanuméricos).",
            )
        return True, cleaned
