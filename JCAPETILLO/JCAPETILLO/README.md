# EcoTech Solutions – Integración Segura de Servicios Externos (TI3021 - ES3)

Extensión en Python orientada a objetos para el sistema de gestión de **EcoTech Solutions**, orientada al consumo seguro de APIs externas (clima e indicadores de tipo de cambio), control de acceso autenticado, manejo robusto de errores y persistencia local en JSON.

## 1. Requisitos e instalación

1. Crear y activar entorno virtual:
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # Linux / macOS:
   source venv/bin/activate
   ```
2. Instalar dependencias oficiales:
   ```bash
   pip install -r requirements.txt
   ```
3. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   ```
4. Ejecutar el sistema desde la raíz del proyecto:
   ```bash
   python -m src.main
   ```

## 2. Arquitectura del sistema (POO)

- `src/config.py` (`Config`): Carga segura de configuración y llaves desde `.env`.
- `src/validators.py` (`InputValidator`): Validación con expresiones regulares y rangos numéricos para usuarios, contraseñas, ciudades, monedas ISO y montos.
- `src/auth.py` (`AuthManager`): Registro e inicio de sesión con contraseñas encriptadas mediante `bcrypt` (con salt aleatorio) y entrada oculta por `getpass`.
- `src/api_client.py` (`BaseAPIClient`, `WeatherService`, `CurrencyService`): Consumo de Open-Meteo y ExchangeRate-API usando `requests` con `timeout`, verificación TLS y manejo centralizado de códigos HTTP (`200`, `400`, `401/403`, `404`, `429`, `500+`).
- `src/storage.py` (`LocalStorage`): Persistencia local segura en `data/`.
- `src/main.py` (`EcoTechApp`): Flujo interactivo con control de acceso estricto (solo usuarios autenticados acceden a consultas y registros).

## 3. Evaluación crítica y ajustes de seguridad al código generado con IA (Criterio 3.1.4)

Durante el desarrollo se utilizaron herramientas de IA para generar borradores iniciales de consumo de APIs y autenticación. Tras auditar el código generado, se detectaron y corrigieron las siguientes vulnerabilidades:

| Hallazgo en borrador inicial de IA | Riesgo de seguridad / estabilidad | Ajuste técnico aplicado y justificación |
| :--- | :--- | :--- |
| **Contraseñas en texto plano o `hashlib.sha256` sin salt** | Exposición directa de credenciales ante acceso al archivo JSON o ataques de diccionario/rainbow tables. | Se reemplazó por `bcrypt` (`rounds=12`) con salt único por usuario y verificación mediante `bcrypt.checkpw`, dificultando ataques de fuerza bruta. |
| **Credenciales de prueba hardcodeadas en `main.py`** | Riesgo de acceso no autorizado si el código se sube a un repositorio remoto. | Se eliminó el usuario hardcodeado y se implementó flujo de registro/login con almacenamiento excluido en `.gitignore` (`data/users.json`). |
| **Llamadas `requests.get(url)` sin `timeout` ni verificación de estado** | El programa podía quedar congelado indefinidamente o lanzar excepciones no controladas ante respuestas `404`/`500`. | Se centralizó en `BaseAPIClient` con `timeout` configurable desde `.env`, `verify=True` y validación explícita de códigos HTTP. |
| **Exposición de errores técnicos (`print(f"Error: {e}")`)** | Filtración de URLs internas, encabezados o trazas del sistema hacia el usuario final. | Se creó la excepción controlada `APIServiceError` que muestra mensajes genéricos y seguros al usuario sin exponer detalles internos. |
| **Entradas de usuario sin validar enviadas directo a la URL** | Riesgo de inyección de parámetros en la URL o consultas malformadas (ej. moneda vacía o montos negativos). | Se implementó `InputValidator` con reglas estrictas (código ISO de 3 letras, rangos positivos y sanitización de nombres de ciudad/proyecto). |
| **Mensajes diferenciados en login ("Usuario no existe" vs "Clave incorrecta")** | Permite enumeración de usuarios válidos registrados en el sistema. | Se unificó en un mensaje genérico (`"Credenciales inválidas"`) y se agregó un límite máximo de intentos fallidos (`MAX_LOGIN_ATTEMPTS`). |
