-- Dispositivos
CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    latitude REAL DEFAULT 0,
    longitude REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cada envio da estação representa uma medição
CREATE TABLE measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,

    -- Momento em que a estação realizou a medição
    measured_at INTEGER NOT NULL,

    -- Momento em que o servidor recebeu a medição
    received_at INTEGER NOT NULL,

    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Valores individuais (flexível!)
CREATE TABLE measurement_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measurement_id INTEGER NOT NULL,
    parameter TEXT NOT NULL,
    value REAL NOT NULL,
    FOREIGN KEY (measurement_id) REFERENCES measurements(id)
);