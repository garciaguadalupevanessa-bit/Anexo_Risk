-- Añade coordenadas geográficas a donaciones para que aparezcan en el mapa.
ALTER TABLE donaciones ADD COLUMN latitud REAL;
ALTER TABLE donaciones ADD COLUMN longitud REAL;
