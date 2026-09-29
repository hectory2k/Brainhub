-- Fixture mínimo para tests de DuckDB en CI.
-- No reemplaza la DB real; solo provee schema y datos
-- suficientes para que los tests no skipeen en GitHub Actions.

CREATE TABLE terminos_raw (
    term VARCHAR,
    frequency INTEGER,
    video VARCHAR
);

INSERT INTO terminos_raw VALUES
    ('model',  10, 'v1'),
    ('torch',   8, 'v1'),
    ('loss',    5, 'v2'),
    ('tensor',  3, 'v2'),
    ('model',   4, 'v2');

CREATE TABLE progreso (
    video VARCHAR,
    estado VARCHAR
);

INSERT INTO progreso VALUES
    ('v1', 'pendiente'),
    ('v2', 'completado');
