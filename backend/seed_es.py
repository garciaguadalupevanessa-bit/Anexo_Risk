"""Seed con datos de prueba en ciudades españolas."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db.database import get_cursor

necesidades = [
    ("Agua potable para barrios afectados", "agua", "Se necesita agua potable urgente en el barrio de Ruzafa", "Carrer de Ruzafa, 34, Valencia", 39.4720, -0.3650, "alta", "abierta"),
    ("Alimentos no perecederos", "alimentos", "Comida enlatada y arroz para familias desplazadas", "Calle Colón, 12, Valencia", 39.4699, -0.3763, "media", "abierta"),
    ("Médicamentos básicos", "parafarmacia", "Paracetamol, ibuprofeno y material de cura", "Av. del Puerto, 8, Valencia", 39.4550, -0.3370, "critica", "abierta"),
    ("Ropa de abrigo", "ropa", "Chaquetas y mantas para familias sin hogar", "Plaza del Ayuntamiento, 1, Valencia", 39.4710, -0.3760, "media", "abierta"),
    ("Productos de higiene", "higiene", "Jabón, champú, pasta de dientes, pañales", "Carrer de la Paz, 20, Valencia", 39.4680, -0.3720, "baja", "abierta"),
    ("Refugio temporal", "refugio", "Habitaciones disponibles para familias afectadas", "Calle de la Reina, 15, Madrid", 40.4168, -3.7038, "alta", "abierta"),
    ("Transporte de suministros", "transporte", "Furgoneta disponible para llevar ayuda a zonas aisladas", "Gran Vía, 42, Madrid", 40.4200, -3.7070, "media", "abierta"),
    ("Agua para mascotas", "agua", "Agua y comida para animales abandonados", "Calle Serrano, 8, Madrid", 40.4350, -3.6890, "baja", "abierta"),
    ("Material de primeros auxilios", "parafarmacia", "Botiquín completo con vendas y desinfectante", "Paseo de Gracia, 15, Barcelona", 41.3920, 2.1650, "alta", "abierta"),
    ("Alimentos para bebés", "alimentos", "Leche de fórmula, papillas y pañales", "La Rambla, 8, Barcelona", 41.3810, 2.1730, "critica", "abierta"),
    ("Mantas y ropa interior", "ropa", "Mantas térmicas y ropa interior limpia", "Calle Major, 22, Palma", 39.5696, 2.6502, "media", "abierta"),
    ("Combustible para generadores", "otros", "Gasolina para generadores de emergencia", "Calle Larios, 5, Málaga", 36.7213, -4.4214, "alta", "cubierta"),
    ("Herramientas de rescate", "otros", "Palas, martillos, cuerdas para operaciones de rescate", "Calle San Fernando, 10, Sevilla", 37.3886, -5.9823, "critica", "abierta"),
    ("Agua embotellada", "agua", "200 litros de agua embotellada para punto de ayuda", "Gran Vía, 28, Bilbao", 43.2630, -2.9350, "media", "abierta"),
    ("Cobijas para refugiados", "ropa", "Cobijas térmicas para personas en albergues", "Alameda de Zumalacárregui, 2, San Sebastián", 43.3183, -1.9812, "alta", "abierta"),
]

donaciones = [
    ("recursos", "Comida", "50 paquetes de comida", "Cruz Roja Valencia", None, "activa", 39.4700, -0.3700),
    ("recursos", "Mantas", "100 mantas térmicas", "Protectora de animales", None, "activa", 39.4650, -0.3800),
    ("recursos", "Medicamentos", "Botiquines de primeros auxilios", "Farmacia Central", None, "activa", 40.4180, -3.7050),
    ("servicios", "Transporte", "Furgoneta 4x4 disponible", "Transportes Madrid", None, "activa", 40.4200, -3.7100),
    ("servicios", "Alojamiento temporal", "3 habitaciones disponibles", "Hostal Sol", None, "activa", 40.4150, -3.7000),
    ("tiempo", "Herramientas", "4 horas/día voluntariado", "Voluntario Madrid", "12345678Z", "activa", 40.4220, -3.6980),
    ("recursos", "Agua", "300 litros de agua", "Distribuidora Barcelona", None, "activa", 41.3900, 2.1680),
    ("recursos", "Comida", "Comida para 200 personas", "Restaurante Solidario", None, "activa", 41.3850, 2.1700),
    ("servicios", "Transporte", "Camión de gran tonelaje", "Logística Emergency", None, "activa", 41.3950, 2.1620),
    ("tiempo", "Apoyo logistico", "6 horas/día en almacén", "Voluntaria Barcelona", "87654321X", "activa", 41.3880, 2.1750),
]

with get_cursor() as cur:
    cur.executemany(
        """INSERT INTO necesidades (titulo, tipo, descripcion, direccion, latitud, longitud, prioridad, estado)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        necesidades,
    )
    cur.executemany(
        """INSERT INTO donaciones (tipo, recurso, cantidad, contacto, dni, estado, latitud, longitud)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        donaciones,
    )

print("Seed completado: 15 necesidades + 10 donaciones en ciudades españolas")
