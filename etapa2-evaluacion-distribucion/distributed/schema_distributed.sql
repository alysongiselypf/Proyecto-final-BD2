-- 4 relaciones vinculadas (rubrica 6.3.1). pedido y detalle_pedido se
-- fragmentan por id_pedido; usuario y medicamento se replican completas.
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
    id_usuario INTEGER NOT NULL REFERENCES usuario(id),
    fecha TIMESTAMP,
    total NUMERIC(10,2)
);

CREATE TABLE detalle_pedido (
    id INTEGER PRIMARY KEY,
    id_pedido INTEGER NOT NULL REFERENCES pedido(id),
    id_medicamento INTEGER NOT NULL REFERENCES medicamento(id),
    cantidad INTEGER,
    subtotal NUMERIC(10,2)
);


