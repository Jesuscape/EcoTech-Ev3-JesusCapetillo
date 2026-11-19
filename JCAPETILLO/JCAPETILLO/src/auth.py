from datetime import datetime, timezone
import bcrypt
from src.config import Config
from src.storage import LocalStorage
from src.validators import InputValidator


class AuthManager:
    """Controla el registro y autenticación de usuarios con contraseñas encriptadas."""

    def __init__(self) -> None:
        self.users_file = Config.USERS_FILE
        self.current_user: str | None = None

    def _load_users(self) -> dict[str, dict]:
        data = LocalStorage.load_json(self.users_file, default={})
        return data if isinstance(data, dict) else {}

    def register_user(self, username: str, password: str) -> tuple[bool, str]:
        valid_user, user_result = InputValidator.validate_username(username)
        if not valid_user:
            return False, user_result

        valid_pass, pass_result = InputValidator.validate_password(password)
        if not valid_pass:
            return False, pass_result

        users = self._load_users()
        user_key = user_result.lower()
        if user_key in users:
            return False, "El usuario ya existe en el sistema."

        # Hash seguro con salt aleatorio usando bcrypt
        hashed_pw = bcrypt.hashpw(
            pass_result.encode("utf-8"), bcrypt.gensalt(rounds=12)
        ).decode("utf-8")

        users[user_key] = {
            "username": user_result,
            "password_hash": hashed_pw,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if not LocalStorage.save_json(self.users_file, users):
            return False, "No se pudo guardar el usuario en el almacenamiento local."

        return True, f"Usuario '{user_result}' registrado correctamente."

    def login(self, username: str, password: str) -> tuple[bool, str]:
        cleaned_user = username.strip().lower()
        if not cleaned_user or not password:
            return False, "Debe ingresar usuario y contraseña."

        users = self._load_users()
        user_record = users.get(cleaned_user)

        # Mensaje genérico para no revelar si el usuario existe o no
        generic_error = "Credenciales inválidas. Verifique usuario y contraseña."
        if not user_record:
            return False, generic_error

        stored_hash = user_record.get("password_hash", "")
        try:
            is_valid = bcrypt.checkpw(
                password.encode("utf-8"), stored_hash.encode("utf-8")
            )
        except ValueError:
            return False, generic_error

        if not is_valid:
            return False, generic_error

        self.current_user = user_record["username"]
        return True, f"Sesión iniciada correctamente. Bienvenido, {self.current_user}."

    def logout(self) -> None:
        self.current_user = None

    def is_authenticated(self) -> bool:
        return self.current_user is not None
