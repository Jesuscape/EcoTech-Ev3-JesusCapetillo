"""EcoTech Solutions - Sistema Seguro de Gestión y Consumo de Servicios Externos (ES3 - TI3021).
Uso:  python main.py          menú interactivo con autenticación obligatoria
      python main.py --demo   demostración automática completa (ES2 + ES3 en memoria)"""
from datetime import date
from getpass import getpass
import sys

from dominio import (
    Credencial,
    DatoInvalidoError,
    Departamento,
    EcoTechError,
    Empleado,
    ErrorAutenticacion,
    ErrorServicioExterno,
    ParteDiario,
    ParticipacionProyecto,
    Perfil,
    Proyecto,
    RegistroDuplicadoError,
    ReporteExcel,
    ReportePDF,
)
from repositorio import (
    ConexionBD,
    ConsultaExternaRepositorio,
    DepartamentoRepositorio,
    EmpleadoRepositorio,
)
from servicios import (
    ClienteHTTP,
    ServicioAutenticacion,
    ServicioCambio,
    ServicioClima,
)


# ---------- Entradas de usuario con validación ----------

def pedir_texto(mensaje, obligatorio=True):
    while True:
        valor = input(mensaje).strip()
        if valor or not obligatorio:
            return valor
        print("  Este dato es obligatorio.")


def pedir_entero(mensaje):
    while True:
        try:
            return int(input(mensaje))
        except ValueError:
            print("  Ingresa un número entero válido.")


def pedir_decimal(mensaje):
    while True:
        try:
            return float(input(mensaje).replace(",", "."))
        except ValueError:
            print("  Ingresa un número válido (ej: 1500000).")


def pedir_fecha(mensaje):
    while True:
        try:
            return date.fromisoformat(input(mensaje).strip())
        except ValueError:
            print("  Fecha inválida. Usa el formato AAAA-MM-DD (ej: 2024-04-01).")


# ---------- Autenticación y registro inicial (Paso 2 - ES3) ----------

def registrar_con_credencial(repo_emp):
    print("\n--- Registro de Empleado y Credencial Segura ---")
    empleado = Empleado(
        pedir_entero("Id del empleado: "),
        pedir_texto("Nombre completo: "),
        pedir_texto("Dirección (opcional): ", False),
        pedir_texto("Teléfono (opcional): ", False),
        pedir_texto("Correo electrónico: "),
        pedir_decimal("Sueldo base (CLP): "),
        pedir_fecha("Fecha de ingreso (AAAA-MM-DD): "),
    )
    usuario = pedir_texto("Nombre de usuario (4-25 caracteres): ")
    clave = getpass("Contraseña (mín. 8 caracteres, 1 mayúscula y 1 número): ")
    confirmacion = getpass("Confirme la contraseña: ")
    if clave != confirmacion:
        raise DatoInvalidoError("Las contraseñas ingresadas no coinciden.")
    perfil = Perfil(pedir_texto("Perfil (ej: Analista, Administrador): "))
    credencial = Credencial(empleado, usuario, clave, perfil)
    repo_emp.registrar_con_credencial(empleado, credencial)
    print(f"Empleado y credencial '{credencial.nombreUsuario}' registrados de forma segura.")


def flujo_autenticacion(auth, repo_emp):
    """Exige iniciar sesión antes de habilitar cualquier funcionalidad del sistema."""
    while not auth.esta_autenticado():
        print("\n=== EcoTech Solutions - Control de Acceso (ES3) ===")
        if not auth.hay_usuarios_registrados():
            print("No existen usuarios registrados aún. Registre el primer usuario para comenzar.")
        print(" 1. Iniciar sesión")
        print(" 2. Registrar nuevo usuario (empleado + credencial encriptada)")
        print(" 0. Salir")
        eleccion = input("Opción: ").strip()

        if eleccion == "0":
            return False
        if eleccion == "2":
            try:
                registrar_con_credencial(repo_emp)
            except EcoTechError as error:
                print(f"No se pudo completar el registro: {error}")
            continue
        if eleccion == "1":
            usuario = input("Usuario: ")
            clave = getpass("Contraseña: ")
            try:
                cred = auth.iniciar_sesion(usuario, clave)
                print(f"Acceso concedido. Bienvenido, {cred.empleado.nombreCompleto} ({cred.perfil.etiqueta}).")
                return True
            except ErrorAutenticacion as error:
                print(f"Error de acceso: {error}")
                if auth.intentos_restantes == 0:
                    print("Se alcanzó el máximo de intentos fallidos. Cerrando acceso por seguridad.")
                    return False
                print(f"Intentos restantes: {auth.intentos_restantes}")
            continue
        print("Opción no válida.")
    return True


# ---------- Acciones ES3: Servicios Externos ----------

def consultar_clima_proyecto(auth, servicio_clima):
    auth.requerir_autenticacion()
    print("\n--- Consulta Climática para Planificación de Proyectos ---")
    proyecto = pedir_texto("Nombre del proyecto: ")
    ciudad = pedir_texto("Ciudad de ejecución (ej: Concepcion, Santiago, Madrid): ")
    resultado = servicio_clima.consultar_clima(proyecto, ciudad, auth.usuario_actual)
    print("\nResultado climático obtenido desde Open-Meteo:")
    print(f"  Proyecto:      {resultado['proyecto']}")
    print(f"  Ubicación:     {resultado['ciudad']}, {resultado['pais']}")
    print(f"  Temperatura:   {resultado['temperatura_c']} °C")
    print(f"  Humedad:       {resultado['humedad_pct']} %")
    print(f"  Estado:        {resultado['estado_clima']}")
    print(f"  Planificación: {resultado['recomendacion']}")
    print("  Persistencia:  Guardado localmente en SQLite (tabla consulta_clima).")


def calcular_pago_internacional(auth, servicio_cambio, repo_emp):
    auth.requerir_autenticacion()
    print("\n--- Cálculo de Pago Internacional (Tipo de Cambio en Tiempo Real) ---")
    proyecto = pedir_texto("Nombre del proyecto internacional: ")
    usar_empleado = input("¿Calcular usando el sueldo de un empleado registrado? (s/n): ").strip().lower()

    id_persona = None
    if usar_empleado == "s":
        empleado = repo_emp.obtener_por_id(pedir_entero("Id del empleado: "))
        id_persona = empleado.idPersona
        moneda_origen = pedir_texto("Moneda del sueldo base (ej: CLP, USD): ")
        monto = empleado.sueldoBase
        print(f"  Empleado: {empleado.nombreCompleto} | Sueldo base: {monto:,.2f} {moneda_origen.upper()}")
    else:
        moneda_origen = pedir_texto("Moneda origen del presupuesto (ej: CLP, USD, EUR): ")
        monto = pedir_decimal(f"Monto en {moneda_origen.upper()}: ")

    moneda_destino = pedir_texto("Moneda de pago del país destino (ej: USD, EUR, BRL, PEN, MXN): ")
    resultado = servicio_cambio.calcular_pago_internacional(
        proyecto, moneda_origen, moneda_destino, monto, auth.usuario_actual, id_persona=id_persona
    )
    print("\nDetalle del pago internacional calculado:")
    print(f"  Proyecto:          {resultado['proyecto']}")
    print(f"  Monto origen:      {resultado['monto_origen']:,.2f} {resultado['moneda_origen']}")
    print(f"  Tasa de cambio:    1 {resultado['moneda_origen']} = {resultado['tasa_cambio']} {resultado['moneda_destino']}")
    print(f"  Monto a pagar:     {resultado['monto_convertido']:,.2f} {resultado['moneda_destino']}")
    print(f"  Actualización API: {resultado['actualizacion_api']}")
    print("  Persistencia:      Guardado localmente en SQLite (tabla pago_internacional).")


def ver_historial_servicios(auth, repo_consultas):
    auth.requerir_autenticacion()
    climas = repo_consultas.listar_climas(limite=5)
    pagos = repo_consultas.listar_pagos(limite=5)

    print(f"\n--- Últimas Consultas Climáticas ({len(climas)}) ---")
    if not climas:
        print("  Sin registros climáticos todavía.")
    for c in climas:
        print(f"  [{c['id_consulta']}] {c['proyecto']} - {c['ciudad']} ({c['pais']}): "
              f"{c['temperatura_c']}°C, {c['humedad_pct']}% hum., {c['estado_clima']}")

    print(f"\n--- Últimos Pagos Internacionales ({len(pagos)}) ---")
    if not pagos:
        print("  Sin registros de pagos internacionales todavía.")
    for p in pagos:
        print(f"  [{p['id_pago']}] {p['proyecto']}: {p['monto_origen']:,.2f} {p['moneda_origen']} -> "
              f"{p['monto_convertido']:,.2f} {p['moneda_destino']} (tasa {p['tasa_cambio']})")

    exportar = input("\n¿Exportar historial a respaldo local JSON en datos/? (s/n): ").strip().lower()
    if exportar == "s":
        ruta = repo_consultas.exportar_historial_json()
        print(f"Respaldo JSON generado en: {ruta}")


# ---------- Acciones ES2: Empleados y Departamentos ----------

def registrar_empleado(auth, repo_emp, repo_dep):
    auth.requerir_autenticacion()
    empleado = Empleado(
        pedir_entero("Id: "), pedir_texto("Nombre completo: "),
        pedir_texto("Dirección: ", False), pedir_texto("Teléfono: ", False),
        pedir_texto("Correo: "), pedir_decimal("Sueldo base: "),
        pedir_fecha("Fecha de ingreso (AAAA-MM-DD): "),
    )
    codigo = pedir_texto("Código de departamento (Enter para ninguno): ", False)
    if codigo:
        empleado.cambiarDepartamento(repo_dep.obtener_por_codigo(int(codigo)))
    repo_emp.guardar(empleado)
    print("Empleado registrado.")


def listar_empleados(auth, repo_emp):
    auth.requerir_autenticacion()
    empleados = repo_emp.listar_activos()
    if not empleados:
        print("No hay empleados registrados.")
    for e in empleados:
        print(" ", e)


def buscar_empleado(auth, repo_emp):
    auth.requerir_autenticacion()
    print(repo_emp.obtener_por_id(pedir_entero("Id a buscar: ")))


def actualizar_empleado(auth, repo_emp):
    auth.requerir_autenticacion()
    empleado = repo_emp.obtener_por_id(pedir_entero("Id del empleado a actualizar: "))
    print("Actual:", empleado)
    empleado.sueldoBase = pedir_decimal("Nuevo sueldo base: ")
    repo_emp.actualizar(empleado)
    print("Empleado actualizado.")


def eliminar_empleado(auth, repo_emp):
    auth.requerir_autenticacion()
    repo_emp.eliminar(pedir_entero("Id del empleado a eliminar: "))
    print("Empleado eliminado.")


def crear_departamento(auth, repo_dep):
    auth.requerir_autenticacion()
    repo_dep.guardar(Departamento(pedir_entero("Código: "), pedir_texto("Nombre: ")))
    print("Departamento creado.")


def listar_departamentos(auth, repo_dep):
    auth.requerir_autenticacion()
    deptos = repo_dep.listar()
    if not deptos:
        print("No hay departamentos registrados.")
    for d in deptos:
        print(" ", d)


def eliminar_departamento(auth, repo_dep):
    auth.requerir_autenticacion()
    repo_dep.eliminar(pedir_entero("Código del departamento a eliminar: "))
    print("Departamento eliminado.")


# ---------- Demostración automática integrada (ES2 + ES3) ----------

def titulo(texto):
    print(f"\n>>> {texto}")


def demostracion():
    bd = ConexionBD(":memory:")
    http = ClienteHTTP(timeout=8)
    try:
        titulo("1. Conexión a la base de datos e inicialización del esquema (ES2 + ES3)")
        print(f"Conexión exitosa a la base de datos (SQLite {bd.probar_conexion()}).")
        bd.inicializar_bd()
        repo_dep = DepartamentoRepositorio(bd)
        repo_emp = EmpleadoRepositorio(bd)
        repo_consultas = ConsultaExternaRepositorio(bd)
        auth = ServicioAutenticacion(repo_emp)
        clima_srv = ServicioClima(http, repo_consultas)
        cambio_srv = ServicioCambio(http, repo_consultas)

        titulo("2. Registro transaccional y autenticación segura (PBKDF2-SHA256 con sal)")
        repo_dep.guardar(Departamento(1, "Sustentabilidad Industrial"))
        jesus = Empleado(10, "Jesús Capetillo", "San Pedro de la Paz", "+56912345678",
                         "jesus@ecotech.cl", 1_500_000, date(2025, 2, 1))
        jesus.cambiarDepartamento(repo_dep.obtener_por_codigo(1))
        repo_emp.registrar_con_credencial(
            jesus, Credencial(jesus, "jcapetillo", "Clave#2026", Perfil("Analista"))
        )
        # Intento de acceso sin autenticación bloqueado
        try:
            auth.requerir_autenticacion()
        except ErrorAutenticacion as error:
            print(f"  Bloqueo sin sesión: {error}")

        # Contraseña errónea rechazada con mensaje genérico
        try:
            auth.iniciar_sesion("jcapetillo", "Incorrecta1")
        except ErrorAutenticacion as error:
            print(f"  Clave errónea rechazada: {error} (intentos restantes: {auth.intentos_restantes})")

        # Inicio de sesión legítimo
        cred = auth.iniciar_sesion("jcapetillo", "Clave#2026")
        print(f"  Sesión autenticada: {cred.nombreUsuario} | Hash: {cred.claveCifrada[:28]}...")

        titulo("3. Validación estricta de entradas para APIs externas (Paso 2)")
        pruebas_validacion = [
            ("Ciudad vacía", lambda: clima_srv.consultar_clima("Parque Solar", "", auth.usuario_actual)),
            ("Ciudad con símbolos", lambda: clima_srv.consultar_clima("Parque Solar", "Concepción; DROP TABLE", auth.usuario_actual)),
            ("Moneda inválida", lambda: cambio_srv.calcular_pago_internacional("Planta Eólica", "CLP", "US1", 1000, auth.usuario_actual)),
            ("Monto negativo", lambda: cambio_srv.calcular_pago_internacional("Planta Eólica", "CLP", "USD", -500, auth.usuario_actual)),
        ]
        for nombre, accion in pruebas_validacion:
            try:
                accion()
            except EcoTechError as error:
                print(f"  {nombre}: {type(error).__name__} -> {error}")

        titulo("4. Manejo controlado de códigos de respuesta HTTP sin exponer datos internos (Paso 3)")
        for codigo in (400, 401, 404, 429, 500):
            try:
                ClienteHTTP.validar_estado_http(codigo)
            except ErrorServicioExterno as error:
                print(f"  HTTP {codigo}: {type(error).__name__} -> {error}")

        titulo("5. Consumo en vivo de APIs externas + persistencia local (Paso 1)")
        try:
            res_clima = clima_srv.consultar_clima("Planta Solar Biobío", "Concepcion", auth.usuario_actual)
            print(f"  Clima [{res_clima['ciudad']}, {res_clima['pais']}]: "
                  f"{res_clima['temperatura_c']}°C, {res_clima['humedad_pct']}% hum., {res_clima['estado_clima']}")
            print(f"  Evaluación operativa: {res_clima['recomendacion']}")
        except ErrorServicioExterno as error:
            print(f"  Clima (error controlado sin caída): {error}")

        try:
            res_pago = cambio_srv.calcular_pago_internacional(
                "Planta Solar Biobío", "CLP", "USD", jesus.sueldoBase, auth.usuario_actual, id_persona=jesus.idPersona
            )
            print(f"  Pago internacional [{jesus.nombreCompleto}]: "
                  f"{res_pago['monto_origen']:,.0f} {res_pago['moneda_origen']} -> "
                  f"{res_pago['monto_convertido']:,.2f} {res_pago['moneda_destino']} (tasa {res_pago['tasa_cambio']})")
        except ErrorServicioExterno as error:
            print(f"  Tipo de cambio (error controlado sin caída): {error}")

        print(f"  Registros guardados en SQLite -> Clima: {len(repo_consultas.listar_climas())}, "
              f"Pagos: {len(repo_consultas.listar_pagos())}")

        titulo("6. Continuidad de ES2: Blindaje SQL, Transacción Rollback y Polimorfismo")
        payload = "' OR '1'='1"
        print(f"  Inyección SQL {payload!r}: {len(repo_emp.buscar_por_nombre(payload))} resultado(s).")
        duplicado = Empleado(11, "Usuario Prueba", "", "", "prueba@ecotech.cl", 1_000_000, date(2025, 3, 1))
        try:
            repo_emp.registrar_con_credencial(
                duplicado, Credencial(duplicado, "jcapetillo", "Clave#2026", Perfil("Analista"))
            )
        except RegistroDuplicadoError as error:
            print(f"  Rollback transaccional comprobado: {error}")

        proyecto = Proyecto(1, "Planta Solar Biobío", "Monitoreo fotovoltaico", date(2025, 2, 1))
        ParticipacionProyecto(jesus, proyecto)
        ParteDiario(1, jesus, proyecto, date(2025, 4, 14), 6.5, "Instalación de sensores")
        for reporte in (ReportePDF("operativo"), ReporteExcel("operativo")):
            texto = reporte.construir([jesus.departamento], [proyecto])
            print(f"  {type(reporte).__name__}.exportar() -> {len(reporte.exportar(texto))} bytes")

    except EcoTechError as error:
        print(f"Error controlado del sistema: {error}")
    finally:
        http.cerrar()
        bd.cerrar()


# ---------- Menú interactivo protegido por autenticación ----------

def menu():
    bd = ConexionBD()
    http = ClienteHTTP()
    try:
        bd.inicializar_bd()
        print(f"Conexión exitosa a la base de datos (SQLite {bd.probar_conexion()}) - {bd.ruta}")
    except EcoTechError as error:
        print(f"No se pudo iniciar el sistema: {error}")
        http.cerrar()
        return

    repo_dep = DepartamentoRepositorio(bd)
    repo_emp = EmpleadoRepositorio(bd)
    repo_consultas = ConsultaExternaRepositorio(bd)
    auth = ServicioAutenticacion(repo_emp)
    servicio_clima = ServicioClima(http, repo_consultas)
    servicio_cambio = ServicioCambio(http, repo_consultas)

    opciones = {
        "1": ("Consultar clima para planificación de proyectos (API externa)",
              lambda: consultar_clima_proyecto(auth, servicio_clima)),
        "2": ("Calcular pago internacional con tipo de cambio actual (API externa)",
              lambda: calcular_pago_internacional(auth, servicio_cambio, repo_emp)),
        "3": ("Ver historial local de consultas y exportar JSON",
              lambda: ver_historial_servicios(auth, repo_consultas)),
        "4": ("Registrar empleado", lambda: registrar_empleado(auth, repo_emp, repo_dep)),
        "5": ("Listar empleados", lambda: listar_empleados(auth, repo_emp)),
        "6": ("Buscar empleado por id", lambda: buscar_empleado(auth, repo_emp)),
        "7": ("Actualizar sueldo de un empleado", lambda: actualizar_empleado(auth, repo_emp)),
        "8": ("Eliminar empleado", lambda: eliminar_empleado(auth, repo_emp)),
        "9": ("Crear departamento", lambda: crear_departamento(auth, repo_dep)),
        "10": ("Listar departamentos", lambda: listar_departamentos(auth, repo_dep)),
        "11": ("Eliminar departamento", lambda: eliminar_departamento(auth, repo_dep)),
        "12": ("Registrar empleado con credencial encriptada (transacción)",
               lambda: registrar_con_credencial(repo_emp)),
        "13": ("Ejecutar demostración automática (ES2 + ES3)", demostracion),
        "14": ("Cerrar sesión", lambda: (auth.cerrar_sesion(), print("Sesión cerrada correctamente."))),
    }

    try:
        while True:
            if not auth.esta_autenticado():
                if not flujo_autenticacion(auth, repo_emp):
                    print("Saliendo del sistema. Hasta pronto.")
                    break
                continue

            print(f"\n=== EcoTech Solutions (Usuario: {auth.usuario_actual} | Perfil: {auth.perfil_actual}) ===")
            for clave, (texto, _) in opciones.items():
                print(f"{clave:>2}. {texto}")
            print(" 0. Salir")
            eleccion = input("Opción: ").strip()
            if eleccion == "0":
                print("Saliendo del sistema. Hasta pronto.")
                break
            if eleccion not in opciones:
                print("Opción no válida.")
                continue
            try:
                opciones[eleccion][1]()
            except EcoTechError as error:
                print(f"No se pudo completar la operación: {error}")
            except ValueError as error:
                print(f"Dato inválido: {error}")
    except (KeyboardInterrupt, EOFError):
        print("\nSesión finalizada de forma segura.")
    finally:
        http.cerrar()
        bd.cerrar()


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demostracion()
    else:
        menu()
