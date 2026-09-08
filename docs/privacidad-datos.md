# Privacy Audit — Anexo_Risk

**Date:** 2026-09-07  
**Status:** Analysis Complete  
**Database:** `anexo_risk.db`

---

## 1. Personal Data Inventory

### 1.1 Data Categories

| Category | Table | Columns | Sensitivity |
|----------|-------|---------|-------------|
| **PII (Personally Identifiable Information)** | | | |
| Full name | `personas` | nombre | HIGH |
| Document ID (DNI) | `personas` | dni | HIGH |
| Document ID (DNI) | `donaciones` | dni | HIGH |
| Email | `personas` | email | HIGH |
| Phone | `personas` | telefono | HIGH |
| Address | `personas` | direccion | MEDIUM |
| Age | `personas` | edad | LOW |
| **Location Data** | | | |
| Home coordinates | `personas` | latitud, longitud | HIGH |
| Last known location | `personas` | ultima_ubicacion | HIGH |
| Need coordinates | `necesidades` | latitud, longitud | MEDIUM |
| Resource coordinates | `resources` | latitud, longitud | MEDIUM |
| Alert coordinates | `alertas` | lat, lon | LOW |
| **Medical/Health Data** | | | |
| Blood type | `personas` | tipo_sangre | HIGH |
| Medical conditions | `personas` | condiciones_medicas | HIGH |
| Allergies | `personas` | alergias | HIGH |
| Medications | `personas` | medicamentos | HIGH |
| Disabilities | `personas` | discapacidades | HIGH |
| **Emergency Contact** | | | |
| Emergency contact name | `personas` | contacto_emergencia_nombre | MEDIUM |
| Emergency contact phone | `personas` | contacto_emergencia_telefono | MEDIUM |
| **Organizational Data** | | | |
| Organization name | `organizations` | name | LOW |
| Organization type | `organizations` | type | LOW |
| Organization region | `organizations` | region | LOW |
| **User Credentials** | | | |
| Username | `operational_users` | username | MEDIUM |
| Role | `operational_users` | role | LOW |
| **Volunteer Data** | | | |
| Volunteer name | `voluntarios` | nombre | HIGH |
| Volunteer DNI | `voluntarios` | dni | HIGH |
| Volunteer email | `voluntarios` | email | HIGH |
| Volunteer phone | `voluntarios` | telefono | HIGH |
| Volunteer address | `voluntarios` | direccion | MEDIUM |
| Volunteer skills | `voluntarios` | habilidades | LOW |
| Volunteer availability | `voluntarios` | disponible | LOW |
| **Financial Data** | | | |
| Donation amount | `donaciones` | monto | MEDIUM |
| Donation status | `donaciones` | estado | LOW |

### 1.2 Data Sensitivity Matrix

| Sensitivity | Tables | Risk Level |
|-------------|--------|------------|
| HIGH | personas, voluntarios | 🔴 Critical |
| MEDIUM | donaciones, operational_users, resources | 🟡 Moderate |
| LOW | organizations, alertas, necesidades | 🟢 Low |

---

## 2. Legal Compliance

### 2.1 Relevant Regulations

| Regulation | Applicability | Requirements |
|------------|---------------|--------------|
| **GDPR** (EU) | If processing EU data subjects | Consent, right to erasure, data portability |
| **CCPA** (California) | If processing CA residents | Opt-out, right to know, delete |
| **Ley 1581 de 2012** (Colombia) | If processing Colombian data | Authorization, purpose, data minimization |
| **Ley 1266 de 2008** (Colombia) | If processing financial data | Habeas data, purpose, security |

### 2.2 Data Processing Legal Basis

| Data Type | Legal Basis | Justification |
|-----------|-------------|---------------|
| PII (nombre, dni) | Consent | User registration |
| Location data | Legitimate interest | Emergency coordination |
| Medical data | Explicit consent | Emergency response |
| Financial data | Contract performance | Donation processing |
| Organizational data | Legitimate interest | Resource coordination |

### 2.3 Required Documentation

| Document | Status | Notes |
|----------|--------|-------|
| Privacy policy | ❌ Not created | Required for compliance |
| Data processing agreement | ❌ Not created | Required for third-party processors |
| Consent forms | ❌ Not created | Required for high-sensitivity data |
| Data retention policy | ❌ Not created | Required for compliance |
| Breach notification procedure | ❌ Not created | Required for GDPR/CCPA |

---

## 3. Data Minimization

### 3.1 Current Data Collection

| Table | Columns | Essential | Excess |
|-------|---------|-----------|--------|
| `personas` | 12 | 6 (nombre, dni, email, telefono, latitud, longitud) | 6 (edad, direccion, tipo_sangre, condiciones_medicas, alergias, medicamentos, discapacidades, contacto_emergencia_*) |
| `voluntarios` | 22 | 8 (nombre, dni, email, telefono, direccion, habilidades, disponible, estado) | 14 (fecha_nacimiento, sexo, ocupacion, experencia, disponibilidad_horas, transporte_propio, idiomas, notas, foto_perfil, latitud, longitud, creado_en, actualizado_en, documento_tipo) |
| `donaciones` | 11 | 5 (nombre, monto, tipo, estado, fecha) | 6 (dni, email, telefono, direccion, notas, metodo_pago) |
| `necesidades` | 17 | 8 (titulo, descripcion, prioridad, estado, cantidad, unidad, latitud, longitud) | 9 (incidente, recurso_requerido, urgencia, notas, direccion, created_at, updated_at, assigned_resource_id, responsible_organization_id, priority_score) |
| `resources` | 12 | 7 (name, type, quantity, available_quantity, status, latitud, longitud) | 5 (description, organization_id, created_at, updated_at, capacity) |

### 3.2 Recommendations

| Table | Recommendation | Priority |
|-------|----------------|----------|
| `personas` | Remove medical data unless explicitly needed | HIGH |
| `voluntarios` | Remove optional fields (fecha_nacimiento, sexo, ocupacion, etc.) | HIGH |
| `donaciones` | Remove PII if not needed for accounting | MEDIUM |
| `necesidades` | Keep only essential fields for emergency coordination | MEDIUM |

---

## 4. Data Retention

### 4.1 Current Retention

| Data Type | Current Retention | Recommended |
|-----------|-------------------|-------------|
| PII (personas) | Indefinite | 30 days after incident |
| Location data | Indefinite | 7 days after incident |
| Medical data | Indefinite | Until incident resolved |
| Financial data | Indefinite | 7 years (legal requirement) |
| Operational data | Indefinite | 1 year |
| Logs | Indefinite | 30 days |

### 4.2 Retention Policy

```sql
-- Delete PII after 30 days
DELETE FROM personas WHERE created_at < DATE('now', '-30 days');

-- Delete location data after 7 days
UPDATE personas SET latitud = NULL, longitud = NULL WHERE created_at < DATE('now', '-7 days');

-- Delete medical data after incident resolution
UPDATE personas SET condiciones_medicas = NULL, alergias = NULL, medicamentos = NULL 
WHERE id IN (SELECT persona_id FROM necesidades WHERE estado = 'resuelta');

-- Keep financial data for 7 years
DELETE FROM donaciones WHERE created_at < DATE('now', '-7 years');

-- Keep operational data for 1 year
DELETE FROM necesidades WHERE created_at < DATE('now', '-1 year');
DELETE FROM resources WHERE created_at < DATE('now', '-1 year');
```

---

## 5. Access Control

### 5.1 Current Access Control

| Table | Access | Control |
|-------|--------|---------|
| `personas` | Read/Write | None (no authentication on routes) |
| `voluntarios` | Read/Write | None |
| `donaciones` | Read/Write | None |
| `necesidades` | Read/Write | None |
| `resources` | Read/Write | None |
| `organizations` | Read/Write | None |
| `operational_users` | Read/Write | JWT authentication |

### 5.2 Recommendations

| Table | Recommendation | Priority |
|-------|----------------|----------|
| `personas` | Add authentication to routes | HIGH |
| `voluntarios` | Add authentication to routes | HIGH |
| `donaciones` | Add authentication to routes | MEDIUM |
| `necesidades` | Add authentication to routes | LOW |
| `resources` | Add authentication to routes | LOW |

---

## 6. Data Security

### 6.1 Current Security Measures

| Measure | Status | Notes |
|---------|--------|-------|
| Encryption at rest | ❌ Not implemented | SQLite files are plaintext |
| Encryption in transit | ⚠️ Partial | HTTPS if deployed with TLS |
| Authentication | ⚠️ Partial | Only on some routes |
| Authorization | ❌ Not implemented | No role-based access control |
| Audit logging | ❌ Not implemented | No data access logs |
| Data masking | ❌ Not implemented | No PII masking in logs |
| Backup encryption | ❌ Not implemented | Backups are plaintext |

### 6.2 Recommendations

| Measure | Recommendation | Priority |
|---------|----------------|----------|
| Encryption at rest | Use SQLCipher for SQLite | MEDIUM |
| Encryption in transit | Deploy with TLS | HIGH |
| Authentication | Add JWT to all routes | HIGH |
| Authorization | Implement RBAC | MEDIUM |
| Audit logging | Log all data access | MEDIUM |
| Data masking | Mask PII in logs | HIGH |
| Backup encryption | Encrypt backups | MEDIUM |

---

## 7. Data Subject Rights

### 7.1 Current Support

| Right | Status | Implementation |
|-------|--------|----------------|
| Right to access | ❌ Not implemented | No API to export user data |
| Right to rectification | ⚠️ Partial | Users can update their data |
| Right to erasure | ❌ Not implemented | No API to delete user data |
| Right to portability | ❌ Not implemented | No export to JSON/CSV |
| Right to restrict processing | ❌ Not implemented | No processing restrictions |
| Right to object | ❌ Not implemented | No objection mechanism |

### 7.2 Required APIs

```python
# Right to access
@router.get("/personas/{id}/export")
async def export_persona_data(id: int):
    """Export all data for a person (GDPR Article 15)."""
    # Return JSON with all personal data
    pass

# Right to erasure
@router.delete("/personas/{id}")
async def delete_persona_data(id: int):
    """Delete all personal data for a person (GDPR Article 17)."""
    # Anonymize or delete all personal data
    pass

# Right to portability
@router.get("/personas/{id}/portable")
async def export_portable_data(id: int):
    """Export data in machine-readable format (GDPR Article 20)."""
    # Return JSON in standard format
    pass
```

---

## 8. Third-Party Processors

### 8.1 Current Processors

| Processor | Data Processed | Purpose | DPA Status |
|-----------|---------------|---------|------------|
| SQLite | All data | Database | N/A (local) |
| GeoRisk Finder | H3 cells, risk scores | Scientific analysis | ❌ Not created |
| H3 library | Coordinates | Spatial indexing | N/A (library) |

### 8.2 Recommendations

| Processor | Recommendation | Priority |
|-----------|----------------|----------|
| GeoRisk Finder | Create DPA | HIGH |
| Cloud provider (if any) | Create DPA | HIGH |
| Email service (if any) | Create DPA | MEDIUM |

---

## 9. Privacy Impact Assessment

### 9.1 High-Risk Processing

| Processing | Risk | Mitigation |
|------------|------|------------|
| Collecting medical data | HIGH | Explicit consent, encryption, access control |
| Collecting location data | HIGH | Purpose limitation, retention limits |
| Sharing data with GeoRisk | MEDIUM | DPA, data minimization, anonymization |
| Storing financial data | MEDIUM | Encryption, access control, retention |

### 9.2 Recommendations

| Processing | Recommendation | Priority |
|------------|----------------|----------|
| Medical data | Remove unless explicitly needed | HIGH |
| Location data | Add retention limits | HIGH |
| GeoRisk sharing | Anonymize data before sharing | HIGH |
| Financial data | Encrypt at rest | MEDIUM |

---

## 10. Action Items

### 10.1 MUST DO (Before next release)

| Action | Owner | Priority | Effort |
|--------|-------|----------|--------|
| Remove medical data from personas | Backend | HIGH | 1 day |
| Add authentication to all routes | Backend | HIGH | 2 days |
| Add data retention policy | Backend | HIGH | 1 day |
| Create privacy policy | Legal | HIGH | 1 day |

### 10.2 SHOULD DO (Next sprint)

| Action | Owner | Priority | Effort |
|--------|-------|----------|--------|
| Implement right to access API | Backend | MEDIUM | 2 days |
| Implement right to erasure API | Backend | MEDIUM | 2 days |
| Add audit logging | Backend | MEDIUM | 2 days |
| Mask PII in logs | Backend | MEDIUM | 1 day |

### 10.3 NICE TO HAVE (Future)

| Action | Owner | Priority | Effort |
|--------|-------|----------|--------|
| Encrypt database at rest | Backend | LOW | 3 days |
| Implement RBAC | Backend | LOW | 5 days |
| Create DPA for GeoRisk | Legal | LOW | 1 day |
| Implement data portability | Backend | LOW | 2 days |

---

## 11. Conclusion

### 11.1 Current Privacy Status

| Category | Status | Risk |
|----------|--------|------|
| Data minimization | ⚠️ Excess data collected | MEDIUM |
| Consent | ❌ Not implemented | HIGH |
| Retention | ❌ No policy | HIGH |
| Access control | ⚠️ Partial | MEDIUM |
| Encryption | ❌ Not implemented | HIGH |
| Data subject rights | ❌ Not implemented | HIGH |

### 11.2 Top 5 Privacy Risks

1. **Medical data stored without explicit consent** (HIGH)
2. **No data retention policy** (HIGH)
3. **No encryption at rest** (HIGH)
4. **No data subject rights implementation** (HIGH)
5. **No privacy policy** (HIGH)

### 11.3 Recommendation

**Address top 5 risks before any public deployment.**

- Remove medical data unless explicitly needed
- Implement data retention policy
- Add encryption at least for backups
- Implement right to access and erasure
- Create privacy policy

**Current deployment (development only) is acceptable with the understanding that:**
- Data is synthetic/test data
- No real PII is being processed
- No public access
- No third-party processors
