# Privacy Policy — Anexo_Risk v2.1

**Effective date:** 2026-09-08
**Version:** 2.1

---

## Data Collection

Anexo_Risk collects and processes the following data:

### Operational Data (Primary)
- Incident reports and status
- Resource locations and availability
- Organization information
- Geographic coordinates for operational mapping
- Event data from external sources (GDACS, FIRMS, USGS, AEMET, etc.)

### Derived Data
- Risk scores (computed from rules and ML)
- H3 spatial indices
- Action areas (computed from incidents)
- Accessibility/routing calculations
- Correlation clusters

### Analytics (Anonymous)
- Feature usage metrics (no PII)
- API endpoint usage counts
- Error rates
- Response times

## Data We Do NOT Collect

- Personal Identifiable Information (PII) of end users
- Individual tracking data
- Financial information
- Health records
- Authentication credentials (stored externally)

## Data Storage

- All data stored in SQLite databases
- No external data transmission except source feeds
- No cloud storage of operational data
- Backup files stored locally

## Data Retention

- Operational data: retained for operational period + 1 year
- Analytics: retained for 90 days
- Backup files: retained for 30 days
- Logs: retained for 30 days

## Data Sharing

- No data shared with third parties
- No data sold or monetized
- No advertising tracking
- Source feeds are read-only (no write-back)

## Security Measures

- JWT authentication for API access
- Rate limiting (120 RPM/IP)
- Input validation on all endpoints
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)
- CORS restricted to configured origins

## User Rights

- Export operational data (JSON)
- Delete operational data (soft delete)
- Access anonymized analytics
- Request data correction

## Contact

For privacy inquiries, contact the development team.

---

This policy applies to Anexo_Risk v2.1 and all subsequent versions until revised.
