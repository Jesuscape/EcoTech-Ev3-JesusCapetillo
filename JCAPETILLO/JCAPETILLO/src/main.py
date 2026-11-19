from getpass import getpass
from src.api_client import APIServiceError, CurrencyService, WeatherService
from src.auth import AuthManager
from src.config import Config
from src.storage import LocalStorage
from src.validators import InputValidator


class EcoTechApp:
    """Interfaz de consola principal del sistema EcoTech Solutions."""

    def __init__(self) -> None:
        self.auth = AuthManager()
        self.weather_service = WeatherService()
        self.currency_service = CurrencyService()

    def run(self) -> None:
        print("=" * 60)
        print("  EcoTech Solutions - Integración Segura de Servicios Externos")
        print("=" * 60)

        while True:
            if not self.auth.is_authenticated():
                should_exit = self._show_auth_menu()
                if should_exit:
                    print("Saliendo del sistema. Hasta pronto.")
                    break
            else:
                self._show_main_menu()

    def _show_auth_menu(self) -> bool:
        print("\n--- ACCESO AL SISTEMA ---")
        print("1. Iniciar sesión")
        print("2. Registrar nuevo usuario")
        print("3. Salir")

        choice = input("Seleccione una opción: ").strip()
        if choice == "1":
            self._handle_login()
        elif choice == "2":
            self._handle_register()
        elif choice == "3":
            return True
        else:
            print("Opción inválida. Seleccione 1, 2 o 3.")
        return False

    def _handle_register(self) -> None:
        print("\n--- REGISTRO DE USUARIO ---")
        username = input("Nuevo usuario (4-25 caracteres): ")
        password = getpass(
            "Contraseña (mín. 8 caracteres, 1 mayúscula y 1 número): "
        )
        confirm = getpass("Confirme la contraseña: ")

        if password != confirm:
            print("Error: Las contraseñas no coinciden.")
            return

        success, message = self.auth.register_user(username, password)
        print(message)

    def _handle_login(self) -> None:
        max_attempts = Config.get_max_login_attempts()
        for attempt in range(1, max_attempts + 1):
            print(f"\n--- INICIO DE SESIÓN (Intento {attempt}/{max_attempts}) ---")
            username = input("Usuario: ")
            password = getpass("Contraseña: ")
            success, message = self.auth.login(username, password)
            print(message)
            if success:
                return
        print("Demasiados intentos fallidos. Acceso temporalmente denegado.")

    def _show_main_menu(self) -> None:
        print(f"\n--- MENÚ PRINCIPAL (Usuario: {self.auth.current_user}) ---")
        print("1. Consultar clima para planificación de proyectos")
        print("2. Calcular pago internacional (tipo de cambio en tiempo real)")
        print("3. Ver historial local de consultas")
        print("4. Cerrar sesión")

        choice = input("Seleccione una opción: ").strip()
        if choice == "1":
            self._handle_weather_query()
        elif choice == "2":
            self._handle_payment_calculation()
        elif choice == "3":
            self._handle_view_history()
        elif choice == "4":
            self.auth.logout()
            print("Sesión cerrada correctamente.")
        else:
            print("Opción inválida. Intente nuevamente.")

    def _handle_weather_query(self) -> None:
        if not self.auth.is_authenticated():
            print("Acceso denegado. Debe iniciar sesión.")
            return

        print("\n--- CONSULTA CLIMÁTICA DE PROYECTO ---")
        raw_project = input("Nombre del proyecto: ")
        valid_proj, project_result = InputValidator.validate_project_name(raw_project)
        if not valid_proj:
            print(f"Error de validación: {project_result}")
            return

        raw_city = input("Ciudad donde se ejecuta el proyecto: ")
        valid_city, city_result = InputValidator.validate_city(raw_city)
        if not valid_city:
            print(f"Error de validación: {city_result}")
            return

        try:
            weather = self.weather_service.get_weather_by_city(city_result)
            weather["proyecto"] = project_result
            weather["consultado_por"] = self.auth.current_user

            print("\nResultado climático:")
            print(f"  Proyecto:      {weather['proyecto']}")
            print(f"  Ubicación:     {weather['ciudad']}, {weather['pais']}")
            print(f"  Temperatura:   {weather['temperatura_c']} °C")
            print(f"  Humedad:       {weather['humedad_pct']} %")
            print(f"  Estado:        {weather['estado_clima']}")
            print(f"  Evaluación:    {weather['recomendacion_operativa']}")

            saved = LocalStorage.append_record(Config.WEATHER_HISTORY_FILE, weather)
            if saved:
                print("Registro guardado localmente en data/clima_historial.json.")
            else:
                print("Advertencia: No se pudo guardar el registro localmente.")
        except APIServiceError as error:
            print(f"No se pudo completar la consulta climática: {error}")

    def _handle_payment_calculation(self) -> None:
        if not self.auth.is_authenticated():
            print("Acceso denegado. Debe iniciar sesión.")
            return

        print("\n--- CÁLCULO DE PAGO INTERNACIONAL ---")
        raw_project = input("Nombre del proyecto: ")
        valid_proj, project_result = InputValidator.validate_project_name(raw_project)
        if not valid_proj:
            print(f"Error de validación: {project_result}")
            return

        raw_base = input("Moneda base del presupuesto (ej: USD, CLP, EUR): ")
        valid_base, base_currency = InputValidator.validate_currency_code(raw_base)
        if not valid_base:
            print(f"Error de validación: {base_currency}")
            return

        raw_target = input("Moneda local de pago del trabajador (ej: CLP, EUR, BRL): ")
        valid_target, target_currency = InputValidator.validate_currency_code(raw_target)
        if not valid_target:
            print(f"Error de validación: {target_currency}")
            return

        raw_amount = input(f"Monto a pagar en {base_currency}: ")
        valid_amount, amount_result = InputValidator.validate_amount(raw_amount)
        if not valid_amount:
            print(f"Error de validación: {amount_result}")
            return

        try:
            payment = self.currency_service.convert_payment(
                base_currency, target_currency, float(amount_result)
            )
            payment["proyecto"] = project_result
            payment["registrado_por"] = self.auth.current_user

            print("\nDetalle del pago internacional:")
            print(f"  Proyecto:          {payment['proyecto']}")
            print(
                f"  Monto base:        {payment['monto_origen']} {payment['moneda_origen']}"
            )
            print(
                f"  Tasa de cambio:    1 {payment['moneda_origen']} = {payment['tasa_cambio']} {payment['moneda_destino']}"
            )
            print(
                f"  Total a pagar:     {payment['monto_convertido']} {payment['moneda_destino']}"
            )
            print(f"  Actualización API: {payment['actualizacion_api']}")

            saved = LocalStorage.append_record(Config.PAYMENTS_HISTORY_FILE, payment)
            if saved:
                print("Registro guardado localmente en data/pagos_historial.json.")
            else:
                print("Advertencia: No se pudo guardar el pago localmente.")
        except APIServiceError as error:
            print(f"No se pudo calcular el pago internacional: {error}")

    def _handle_view_history(self) -> None:
        if not self.auth.is_authenticated():
            print("Acceso denegado. Debe iniciar sesión.")
            return

        weather_records = LocalStorage.load_json(Config.WEATHER_HISTORY_FILE, [])
        payment_records = LocalStorage.load_json(Config.PAYMENTS_HISTORY_FILE, [])

        print(f"\n--- HISTORIAL DE CLIMA ({len(weather_records)} registros) ---")
        for item in weather_records[-5:]:
            print(
                f"  - [{item.get('proyecto')}] {item.get('ciudad')}: "
                f"{item.get('temperatura_c')}°C, {item.get('humedad_pct')}% hum., {item.get('estado_clima')}"
            )

        print(f"\n--- HISTORIAL DE PAGOS ({len(payment_records)} registros) ---")
        for item in payment_records[-5:]:
            print(
                f"  - [{item.get('proyecto')}] {item.get('monto_origen')} {item.get('moneda_origen')} "
                f"-> {item.get('monto_convertido')} {item.get('moneda_destino')} "
                f"(tasa: {item.get('tasa_cambio')})"
            )


if __name__ == "__main__":
    app = EcoTechApp()
    app.run()
