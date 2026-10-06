-- 4 relaciones vinculadas minimas exigidas por la rubrica 6.3.1
DROP TABLE IF EXISTS detalle_pedido CASCADE;
DROP TABLE IF EXISTS pedido CASCADE;
DROP TABLE IF EXISTS medicamento CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;

CREATE TABLE usuario (
    id INTEGER PRIMARY KEY,
    nombres VARCHAR(100),
    apellidos VARCHAR(100)
);

CREATE TABLE medicamento (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(100),
    precio NUMERIC(10,2)
);

CREATE TABLE pedido (
    id INTEGER PRIMARY KEY,
    id_usuario INTEGER,
    fecha TIMESTAMP,
    total NUMERIC(10,2)
);

CREATE TABLE detalle_pedido (
    id INTEGER PRIMARY KEY,
    id_pedido INTEGER,
    id_medicamento INTEGER,
    cantidad INTEGER,
    subtotal NUMERIC(10,2)
);
