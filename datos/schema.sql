-- Esquema relacional de EcoTech Solutions (SQLite - ES2 + ES3)
-- La integridad referencial se activa en cada conexión con PRAGMA foreign_keys = ON

CREATE TABLE IF NOT EXISTS departamento (
    codigo_depto INTEGER PRIMARY KEY,
    nombre_depto TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS empleado (
    id_persona      INTEGER PRIMARY KEY,
    nombre_completo TEXT NOT NULL,
    direccion       TEXT,
    telefono        TEXT,
    correo          TEXT NOT NULL UNIQUE,
    sueldo_base     REAL NOT NULL CHECK (sueldo_base > 0),
    fecha_ingreso   TEXT NOT NULL,
    codigo_depto    INTEGER,
    activo          INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
    FOREIGN KEY (codigo_depto) REFERENCES departamento (codigo_depto) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS credencial (
    nombre_usuario TEXT PRIMARY KEY,
    clave_cifrada  TEXT NOT NULL,
    habilitada     INTEGER NOT NULL DEFAULT 1 CHECK (habilitada IN (0, 1)),
    perfil         TEXT NOT NULL,
    id_persona     INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (id_persona) REFERENCES empleado (id_persona) ON DELETE CASCADE
);

-- Tablas de persistencia local para servicios externos (Unidad 3 - ES3)

CREATE TABLE IF NOT EXISTS consulta_clima (
    id_consulta      INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto         TEXT NOT NULL,
    ciudad           TEXT NOT NULL,
    pais             TEXT NOT NULL,
    temperatura_c    REAL NOT NULL,
    humedad_pct      INTEGER NOT NULL,
    estado_clima     TEXT NOT NULL,
    recomendacion    TEXT NOT NULL,
    usuario_consulta TEXT NOT NULL,
    fecha_utc        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pago_internacional (
    id_pago          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_persona       INTEGER,
    proyecto         TEXT NOT NULL,
    moneda_origen    TEXT NOT NULL,
    moneda_destino   TEXT NOT NULL,
    monto_origen     REAL NOT NULL CHECK (monto_origen > 0),
    tasa_cambio      REAL NOT NULL CHECK (tasa_cambio > 0),
    monto_convertido REAL NOT NULL CHECK (monto_convertido > 0),
    usuario_registro TEXT NOT NULL,
    fecha_utc        TEXT NOT NULL,
    FOREIGN KEY (id_persona) REFERENCES empleado (id_persona) ON DELETE SET NULL
);
