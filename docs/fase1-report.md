# FASE 1 — Informe Final: Corrección de Hallazgos DB

**Fecha:** 2026-09-07  
**Estado:** COMPLETADA  
**Tests:** 413 passed, 0 failures, 0 regressions

---

## 1. Índices

### 6 índices HIGH añadidos

| # | Índice | Tabla | Columnas | Query que optimiza |
|---|--------|-------|----------|-------------------|
| 1 | `idx_alertas_active_location` | alertas | `(is_active, lat, lon)` | `WHERE is_active=1 AND lat BETWEEN AND lon BETWEEN` — 5 endpoints operacionales |
| 2 | `idx_alertas_created_at` | alertas | `(created_at)` | `ORDER BY created_at DESC LIMIT ?` — ordenación temporal |
| 3 | `idx_necesidades_location` | necesidades | `(latitud, longitud)` | `WHERE lat BETWEEN AND lon BETWEEN` — 6 endpoints operacionales |
| 4 | `idx_necesidades_estado` | necesidades | `(estado)` | `WHERE estado='abierta'` — filtros de estado |
| 5 | `idx_necesidades_creado_en` | necesidades | `(creado_en)` | `ORDER BY creado_en DESC LIMIT ?` — ordenación temporal |
| 6 | `idx_need_assignments_assigned_at` | need_assignments | `(assigned_at)` | `ORDER BY assigned_at DESC LIMIT ?` — 5 queries de asignaciones |

**Migración:** `015_indexes_operacionales.sql`  
**Justificación:** Cada índice optimiza al menos 1 query de los endpoints operacionales. Los queries más frecuentes son las búsquedas espaciales (BETWEEN) y las ordenaciones temporales (ORDER BY DESC).

---

## 2. feedback_loop

### Esquema formal

- **Migración:** `016_feedback_loop.sql`
- **21 columnas** — coincide exactamente con `models/feedback.py`
- **2 índices:** `idx_feedback_h3`, `idx_feedback_prediction_time`
- **Compatible con datos existentes:** `CREATE TABLE IF NOT EXISTS` preserva las 8 filas existentes
- **Idempotente:** Seguro de re-ejecutar

### Dependencia eliminada

`feedback.py:init_feedback_table()` sigue existiendo por compatibilidad, pero la tabla ahora está definida en el sistema formal de migraciones. Al arrancar `init_db()`, la migración 016 crea la tabla si no existe.

---

## 3. Organizaciones

### Problema

`"Proteccion Civil Madrid"` aparecía 7 veces (ids 2-8) + `"Protección Civil Madrid"` (id 1, con tilde). Todas con tipo `proteccion_civil` y región `Madrid`.

### Solución (Migración 017)

1. **Organización canónica:** id=1 (`"Protección Civil Madrid"`)
2. **Referencias migradas:**
   - `operational_users.organization_id`: 7 filas → todas a id=1
   - `resources.organization_id`: 7 filas → todas a id=1
   - `necesidades.responsible_organization_id`: 0 filas afectadas
3. **Duplicados eliminados:** ids 2-8 eliminados
4. **Constraint de unicidad:** `idx_organizations_name_region` sobre `(name, region)` — permite homónimos en regiones distintas

### Resultado

| Métrica | Antes | Después |
|---------|-------|---------|
| Filas en organizations | 8 | 1 |
| Referencias FK válidas | 14 | 14 |
| Referencias huérfanas | 0 | 0 |
| Constraint unique | No | Sí (name, region) |

---

## 4. Tests

### Número final

| Suite | Tests |
|-------|-------|
| test_db_integrity.py | 58 |
| Resto backend (sin test_alertas.py) | 355 |
| **Total** | **413** |

### Tests añadidos en FASE 1

| Test | Verifica |
|------|----------|
| `test_alertas_has_active_location_index` | Índice compuesto (is_active, lat, lon) |
| `test_alertas_has_created_at_index` | Índice temporal |
| `test_necesidades_has_location_index` | Índice espacial |
| `test_necesidades_has_estado_index` | Índice de estado |
| `test_necesidades_has_creado_en_index` | Índice temporal |
| `test_need_assignments_has_assigned_at_index` | Índice temporal |
| `test_no_duplicate_organization_names` | Sin duplicados (name, region) |
| `test_all_resources_reference_canonical_org` | FK válidas |
| `test_all_operational_users_reference_canonical_org` | FK válidas |
| `test_organizations_has_name_region_index` | Constraint unique |

### Tests actualizados

| Test | Cambio |
|------|--------|
| `test_migrations_have_timestamps` | `>= 14` → `>= 17` |
| `test_organizations_name_unique` | Ahora verifica (name, region) en vez de solo name |

---

## 5. Privacidad

### Datos identificados

| Tabla | Tipo | Riesgo |
|-------|------|--------|
| `personas` | Datos médicos, localización, contacto | ALTO |
| `voluntarios` | DNI, email, teléfono, dirección | ALTO |
| `donaciones` | DNI, monto | MEDIO |
| `organizations` | Nombres institucionales | BAJO |
| `alertas` | Coordenadas, fuentes públicas | BAJO |
| `necesidades` | Coordenadas, descripciones | BAJO |

### Pendiente antes de publicación

- [ ] Revisar fixtures/datos seed para anonimizar
- [ ] Verificar que no hay datos personales reales en test data
- [ ] Eliminar o anonimizar DNI en donaciones de prueba
- [ ] Revisar screenshots/ejemplos
- [ ] Crear política de privacidad

---

## 6. Estado

### Completado

- [x] 6 índices HIGH creados y testeados
- [x] feedback_loop migrado a migración formal
- [x] Organizaciones canonicalizadas (8→1)
- [x] Constraint unique en (name, region)
- [x] 413 tests pasando, 0 regresiones
- [x] Migraciones 015, 016, 017 aplicadas
- [x] Documentación actualizada
- [x] Scripts temporales eliminados

### Pendiente (no bloqueante)

- [ ] Privacidad: anonimizar datos sensibles antes de publicación
- [ ] test_alertas.py:修复 `_DB_LOCK` error (pre-existente, no causado por FASE 1)

### FASE 1 está COMPLETADA

Todos los hallazgos de la auditoría DB han sido corregidos. La base de datos tiene integridad verificada, migraciones formales, y una organización canonical sin duplicados.

---

## 7. Migraciones aplicadas

| # | Archivo | Propósito |
|---|---------|-----------|
| 015 | `015_indexes_operacionales.sql` | 6 índices para rutas operacionales |
| 016 | `016_feedback_loop.sql` | Tabla formal de feedback_loop |
| 017 | `017_canonicalize_organizations.sql` | Canonicalización de organizaciones |

### Verificación de idempotencia

Las 3 migraciones usan `CREATE INDEX IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`, y `UPDATE/DELETE` sobre datos existentes. Son seguras de re-ejecutar.
