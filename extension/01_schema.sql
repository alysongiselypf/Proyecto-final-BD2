-- =========================================================
-- Esquema Farmacia — traducido de MariaDB a PostgreSQL 18
-- Proyecto Final BD2: Extendible Hashing sobre PostgreSQL
-- =========================================================

DROP TABLE IF EXISTS usuario CASCADE;
CREATE TABLE usuario (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo_documento    VARCHAR(20)  NOT NULL,
    numero_documento  VARCHAR(20)  NOT NULL UNIQUE,
    fecha_nacimiento  DATE         NOT NULL,
    nombres           VARCHAR(100) NOT NULL,
    apellidos         VARCHAR(100) NOT NULL,
    telefono          VARCHAR(15)  NOT NULL,
    password          VARCHAR(255) NOT NULL,
    rol               VARCHAR(20)  NOT NULL DEFAULT 'paciente'
                        CHECK (rol IN ('paciente','doctor','administrador')),
    especialidad      VARCHAR(100),
    id_departamento   INTEGER,
    creado_en         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS medicamento CASCADE;
CREATE TABLE medicamento (
    id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre  VARCHAR(100) NOT NULL,
    clase   VARCHAR(100),
    stock   INTEGER DEFAULT 0,
    precio  NUMERIC(10,2) NOT NULL,
    imagen  VARCHAR(100),
    tipo    VARCHAR(20) DEFAULT 'medicamento'
              CHECK (tipo IN ('medicamento','suplemento'))
);

DROP TABLE IF EXISTS pedido CASCADE;
CREATE TABLE pedido (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario    INTEGER NOT NULL REFERENCES usuario(id),
    fecha         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nombre_envio  VARCHAR(100),
    direccion     VARCHAR(200),
    ciudad        VARCHAR(100),
    telefono      VARCHAR(20),
    total         NUMERIC(10,2),
    estado        VARCHAR(30) DEFAULT 'completado'
);

DROP TABLE IF EXISTS detalle_pedido CASCADE;
CREATE TABLE detalle_pedido (
    id               INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pedido        INTEGER NOT NULL REFERENCES pedido(id),
    id_medicamento   INTEGER REFERENCES medicamento(id),
    nombre_producto  VARCHAR(100),
    cantidad         INTEGER,
    precio_unitario  NUMERIC(10,2),
    subtotal         NUMERIC(10,2)
);

DROP TABLE IF EXISTS cita CASCADE;
CREATE TABLE cita (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_paciente INTEGER NOT NULL REFERENCES usuario(id),
    id_doctor   INTEGER NOT NULL REFERENCES usuario(id),
    fecha_cita  DATE NOT NULL,
    hora_cita   TIME NOT NULL,
    motivo      VARCHAR(255),
    estado      VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                  CHECK (estado IN ('pendiente','atendida','cancelada')),
    creado_en   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS consulta CASCADE;
CREATE TABLE consulta (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cita         INTEGER NOT NULL REFERENCES cita(id),
    id_paciente     INTEGER NOT NULL REFERENCES usuario(id),
    id_doctor       INTEGER NOT NULL REFERENCES usuario(id),
    fecha_consulta  DATE NOT NULL,
    motivo          VARCHAR(255),
    diagnostico     TEXT NOT NULL,
    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS receta CASCADE;
CREATE TABLE receta (
    id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_consulta     INTEGER NOT NULL REFERENCES consulta(id),
    id_medicamento  INTEGER NOT NULL REFERENCES medicamento(id),
    dosis           VARCHAR(255) NOT NULL,
    instrucciones   TEXT,
    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO usuario (tipo_documento, numero_documento, fecha_nacimiento, nombres, apellidos, telefono, password, rol, especialidad, id_departamento, creado_en) VALUES
('DNI','72471842','2004-11-24','Alyson','Perez Flores','999444777','$2y$10$yZnO3FZ6Ny8eGLfjnysUSum7H0ojih8D2GNJo4IT7mRqgp8wtwNfy','paciente',NULL,NULL,'2026-06-18 22:39:19'),
('DNI','60820045','2005-11-12','Alejandra','Torres Garcia','951478236','$2y$10$BA4sZdLUXlgfWzNovrngM.BOsIDu3exmnwHl1ICM1UhHZd1t0vWSa','paciente',NULL,NULL,'2026-06-19 02:51:17'),
('DNI','12345678','1994-05-14','Luis','Fernandez','956789123','$2y$10$f/uoC/LQPYqu7nG.6OvuM.Z3IlfnTLcMdA6sNP9BFD6JGQGIRlMR2','doctor','Pediatria',NULL,'2026-06-20 00:55:34'),
('DNI','45678901','1997-05-18','Ana','Mendoza','978123456','$2y$10$SKWoBvGLqeCrPefWTn76BuR/HyggmqpyWqJ5ePnwBt7xJqiTWf2GC','administrador',NULL,NULL,'2026-06-20 00:57:58'),
('DNI','78901234','1995-08-15','Miguel','Herrera','987123654','$2y$10$iyLbVDQcKB3OzZdOyfGVFOaBuhojqifMYgNI8wz1RQd./A67mW3nu','doctor','Cardiologia',NULL,'2026-06-20 01:32:04');

INSERT INTO medicamento (nombre, clase, stock, precio, imagen, tipo) VALUES
('Paracetamol','Analgesico',149,10.00,'im1.png','medicamento'),
('Amoxicilina','Antibiotico',199,12.90,'im2.png','medicamento'),
('Ibuprofeno','Antiinflamatorio',179,9.00,'im3.png','medicamento'),
('Omeprazol','Gastroprotector',119,16.00,'im4.png','medicamento'),
('Loratadina','Antihistaminico',119,4.00,'im5.png','medicamento'),
('Metformina','Antidiabetico',299,24.50,'im6.png','medicamento'),
('Enalapril','Antihipertensivo',133,6.00,'im7.png','medicamento'),
('Simvastatina','Hipolipemiante',160,37.50,'im8.png','medicamento'),
('Furosemida','Diuretico',90,10.00,'im9.png','medicamento'),
('Clopidogrel','Antiplaquetario',75,15.30,'im10.png','medicamento'),
('Vitamina D','Suplemento vitaminico',250,50.90,'im11.jpg','suplemento'),
('Omega-3','Suplemento',200,73.80,'im12.jpg','suplemento'),
('Multivitaminico','Suplemento vitaminico',200,75.90,'im13.jpg','suplemento'),
('Calcio','Suplemento mineral',180,47.90,'im14.jpg','suplemento'),
('Magnesio','Suplemento mineral',150,94.90,'im15.jpg','suplemento'),
('Zinc','Suplemento mineral',220,39.90,'im16.jpg','suplemento'),
('Vitamina B12','Suplemento vitaminico',160,59.90,'im17.jpg','suplemento'),
('Probioticos','Suplemento digestivo',100,93.90,'im18.jpg','suplemento'),
('Vitamina C','Suplemento vitaminico',270,29.80,'im19.jpg','suplemento'),
('Colageno','Suplemento',140,34.90,'im20.jpg','suplemento'),
('Aspirina','Analgesico',200,8.50,'img_1781924121_6a3601197d85e.png','medicamento'),
('Zinc Plus','Suplemento Mineral',150,45.90,'img_1781924325_6a3601e5be57a.jpeg','suplemento'),
('Probioticos Digest','Suplemento digestivo',90,49.90,'img_1781924996_6a360484e4999.jpeg','suplemento');

INSERT INTO pedido (id_usuario, fecha, nombre_envio, direccion, ciudad, telefono, total, estado) VALUES
(1,'2026-06-18 20:21:08','Alyson Perez','Av. principal 123','Arequipa','999888777',12.90,'completado'),
(1,'2026-06-18 20:38:49','Juan Garcia','Av. peru 123','Arequipa','999555111',26.00,'completado'),
(1,'2026-06-18 21:15:31','Maria Medina','Av. arequipa 753','Arequipa','999447586',31.90,'completado'),
(1,'2026-06-18 21:18:54','Juana Castro','Av. progreso 489','Arequipa','995847159',44.50,'completado'),
(2,'2026-06-18 22:00:12','Alejandra Torres','Av. peru 123','Arequipa','995847159',31.90,'completado');

INSERT INTO detalle_pedido (id_pedido, id_medicamento, nombre_producto, cantidad, precio_unitario, subtotal) VALUES
(1,2,'Amoxicilina',1,12.90,12.90),
(2,1,'Paracetamol',1,10.00,10.00),
(2,4,'Omeprazol',1,16.00,16.00),
(3,1,'Paracetamol',1,10.00,10.00),
(3,2,'Amoxicilina',1,12.90,12.90),
(3,3,'Ibuprofeno',1,9.00,9.00),
(4,5,'Loratadina',1,4.00,4.00),
(4,4,'Omeprazol',1,16.00,16.00),
(4,6,'Metformina',1,24.50,24.50),
(5,1,'Paracetamol',1,10.00,10.00),
(5,2,'Amoxicilina',1,12.90,12.90),
(5,3,'Ibuprofeno',1,9.00,9.00);

INSERT INTO cita (id_paciente, id_doctor, fecha_cita, hora_cita, motivo, estado, creado_en) VALUES
(1,3,'2026-06-26','11:00:00','Control General','atendida','2026-06-25 23:52:11'),
(1,5,'2026-06-27','13:30:00','Control General','atendida','2026-06-26 00:56:33');

INSERT INTO consulta (id_cita, id_paciente, id_doctor, fecha_consulta, motivo, diagnostico, creado_en) VALUES
(1,1,3,'2026-06-26','Control General','Paciente en buen estado general. Se realiza control medico de rutina, sin hallazgos de importancia. Se recomienda continuar con habitos saludables y seguimiento periodico.','2026-06-25 23:59:07'),
(2,1,5,'2026-06-27','Control General','Evaluacion de rutina, paciente estable y sin complicaciones.','2026-06-26 01:02:05');

INSERT INTO receta (id_consulta, id_medicamento, dosis, instrucciones, creado_en) VALUES
(2,18,'1 dosis al dia','Tomar antes de comer','2026-06-26 01:02:05');
