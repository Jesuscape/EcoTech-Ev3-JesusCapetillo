# EcoTech Solutions – Integración Segura de Servicios Externos (ES3 - TI3021)

Extensión individual de la aplicación de **EcoTech Solutions** (continuidad de las Unidades 1 y 2) desarrollada en Python bajo **Programación Orientada a Objetos Segura**. Incorpora el consumo de servicios externos en tiempo real (clima para planificación operativa e indicadores de tipo de cambio para pagos internacionales), control de acceso autenticado, validación estricta de entradas, manejo de errores HTTP y persistencia local en SQLite y JSON.

**Autor:** Jesús Capetillo  
**Asignatura:** TI3021 – Programación Orientada a Objeto Seguro (INACAP, Sede San Pedro de la Paz)  
**Evaluación:** Evaluación Sumativa N°3 (ES3)

---

## 1. Arquitectura del Proyecto (Separación por Capas)

El sistema mantiene la arquitectura limpia de la ES2 e incorpora la capa `servicios/` para aislar las comunicaciones HTTP y la lógica de sesión:

```text
JCAPETILLO/
├── datos/
│   └── schema.sql                 # Tablas SQLite (ES2 + consulta_clima y pago_internacional)
├── dominio/
│   ├── persona.py / empleado.py   # Herencia y encapsulamiento (ES2)
│   ├── departamento.py / ...      # Clases del modelo UML validado
│   ├── gestor_cifrado.py          # Hash PBKDF2-SHA256 con sal aleatoria y compare_digest
│   ├── credencial.py              # Validación de acceso y política de clave segura
│   ├── validaciones.py            # Reglas estrictas (usuario, clave, ciudad, moneda ISO, montos)
│   └── excepciones.py             # Jerarquía EcoTechError + errores de autenticación y APIs
├── repositorio/
│   ├── conexion.py                # Conexión SQLite + carga segura de variables .env
│   ├── base_repo.py               # Ejecución parametrizada (?) y rollback
│   ├── empleado_repo.py           # CRUD Empleado + transacción atómica con Credencial
│   ├── departamento_repo.py       # CRUD Departamento
│   └── consulta_repo.py           # Persistencia local de clima/pagos en SQLite y respaldo JSON
├── servicios/
│   ├── cliente_http.py            # Cliente HTTP oficial (requests) con timeout, TLS y códigos HTTP
│   ├── autenticacion_service.py   # Inicio de sesión seguro, límite de intentos y control de acceso
│   ├── clima_service.py           # Consumo de Open-Meteo y alerta operativa para proyectos
│   └── cambio_service.py          # Consumo de ExchangeRate-API y cálculo de pagos internacionales
├── .env.example                   # Plantilla de configuración sin secretos reales
├── .gitignore                     # Excluye .env, __pycache__, *.db, venv y respaldos JSON
├── requirements.txt               # Dependencia oficial: requests
├── main.py                        # Interfaz de consola protegida por login y modo --demo
└── README.md                      # Documentación técnica y bitácora de auditoría IA
```

---

## 2. Requisitos e Instalación

1. Crear y activar un entorno virtual:
   ```bash
   python -m venv venv
   # Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # Linux / macOS:
   source venv/bin/activate
   ```
2. Instalar la librería oficial para consumo de APIs:
   ```bash
   pip install -r requirements.txt
   ```
3. (Opcional) Copiar la plantilla de configuración local:
   ```bash
   copy .env.example .env
   ```
4. Ejecutar el sistema:
   - **Demostración automática (ES2 + ES3):**
     ```bash
     python main.py --demo
     ```
   - **Menú interactivo (con inicio de sesión obligatorio):**
     ```bash
     python main.py
     ```

---

## 3. Servicios Externos Integrados (Criterio 3.1.1)

- **Clima para planificación operativa (`servicios/clima_service.py`):** Consume la API pública de **Open-Meteo** (Geocoding + Forecast) mediante `requests`, obteniendo temperatura (`°C`), humedad relativa (`%`) y estado meteorológico en formato JSON. Evalúa automáticamente si las condiciones son favorables o requieren reprogramar actividades en terreno, y guarda cada consulta en la tabla `consulta_clima`.
- **Pagos internacionales (`servicios/cambio_service.py`):** Consume **ExchangeRate-API v6** para consultar tipos de cambio vigentes en tiempo real. Permite convertir directamente el `sueldoBase` de un empleado registrado en la base de datos o un monto de proyecto hacia la moneda local del país de ejecución, registrando el cálculo en la tabla `pago_internacional`.

---

## 4. Mecanismos de Seguridad y Manejo de Errores (Criterios 3.1.2 y 3.1.3)

- **Autenticación con credenciales encriptadas:** Todas las funcionalidades requieren sesión activa (`ServicioAutenticacion`). Las contraseñas nunca se almacenan en texto plano: se encriptan con **PBKDF2-SHA256** (100.000 iteraciones + sal aleatoria de 16 bytes) y se comparan en tiempo constante (`hmac.compare_digest`). La entrada por consola se oculta con `getpass`, los mensajes de error de login son genéricos (evitan enumeración de usuarios) y existe un límite configurable de intentos fallidos (`ECOTECH_MAX_INTENTOS_LOGIN`).
- **Validación estricta de entradas:** `dominio/validaciones.py` valida con expresiones regulares y rangos numéricos usuarios, contraseñas (mínimo 8 caracteres, una mayúscula y un dígito), nombres de ciudad, nombres de proyecto, códigos ISO de moneda (3 letras) y montos positivos.
- **Resguardo de datos sensibles:** Las configuraciones y llaves opcionales de API se leen desde variables de entorno (`.env` excluido en `.gitignore`) mediante `cargar_env()`.
- **Manejo robusto de errores HTTP:** `ClienteHTTP` aplica `timeout` configurable y verificación TLS (`verify=True`), captura excepciones específicas de `requests` (`Timeout`, `ConnectionError`, `RequestException`) y errores de parseo JSON (`ValueError`), y valida explícitamente códigos HTTP (`200`, `400`, `401/403`, `404`, `429`, `500+`). Ningún mensaje de error expone URLs, encabezados, rutas internas ni trazas del sistema.

---

## 5. Evaluación Crítica y Ajustes al Código Generado con IA (Criterio 3.1.4)

Durante el desarrollo se utilizaron herramientas de IA generativa como apoyo para estructurar los borradores iniciales del consumo de APIs y del flujo de autenticación. Cada fragmento fue auditado y refinado aplicando criterios técnicos de seguridad y arquitectura:

| Fragmento o sugerencia inicial de IA | Aspecto analizado | Decisión | Justificación técnica y ajuste aplicado |
| :--- | :--- | :--- | :--- |
| Borrador inicial sugería crear un proyecto aislado en `src/` sin integrar las clases de ES2 y usar `bcrypt` + `python-dotenv`. | Continuidad arquitectónica y dependencias | **Descarto y adapto** | Se mantuvo la arquitectura por capas de ES2 (`dominio/`, `repositorio/`, `datos/`) agregando `servicios/`, reutilizando `GestorCifrado` (PBKDF2-SHA256) y `cargar_env()` propios de la biblioteca estándar, dejando solo `requests` como dependencia externa oficial. |
| Primer código de consumo HTTP usaba `requests.get(url)` sin `timeout`, sin `verify=True` y con `except Exception as e: print(e)`. | Disponibilidad y fuga de información | **Modifico** | Se creó `ClienteHTTP` con `timeout` configurable desde `.env`, verificación TLS explícita, captura de excepciones específicas (`Timeout`, `ConnectionError`, `RequestException`, `ValueError`), validación de códigos HTTP y mensajes sanitizados mediante `ErrorServicioExterno`. |
| Borrador inicial de login incluía un usuario administrador hardcodeado (`admin` / `123456`) y diferenciaba `"Usuario no existe"` de `"Contraseña incorrecta"`. | Seguridad de credenciales | **Descarto y modifico** | Se eliminó cualquier credencial fija en el código fuente, se exigió registro seguro con `getpass` y política de contraseña fuerte, se unificó el mensaje de error genérico para evitar enumeración de usuarios y se incorporó límite máximo de intentos. |
| Consultas a las APIs concatenaban directamente el texto ingresado por el usuario en la URL sin validación previa. | Validación de entradas | **Modifico** | Se extendió `dominio/validaciones.py` con validadores dedicados (`ciudad_valida`, `codigo_moneda_valido`, `proyecto_valido`) que rechazan caracteres especiales, valores vacíos o códigos de moneda malformados antes de realizar cualquier solicitud HTTP. |
| Sugerencia de guardar historial de APIs únicamente en archivos de texto sin relación con los empleados del sistema. | Persistencia e integridad | **Modifico** | Se añadieron las tablas `consulta_clima` y `pago_internacional` (con llave foránea hacia `empleado`) en `datos/schema.sql`, usando consultas 100% parametrizadas en `repositorio/consulta_repo.py` y ofreciendo además exportación opcional a JSON. |
