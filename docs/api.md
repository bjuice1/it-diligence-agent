# IT Due Diligence Agent - API Reference

## Base URL

```
http://localhost:5001  (development)
https://your-app.railway.app  (production)
```

## Health & Status

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "checks": {
    "api_key": true,
    "output_dir": true
  }
}
```

### GET /api/status
Get current analysis status.

**Response:**
```json
{
  "status": "running",
  "progress": 45,
  "current_phase": "discovery",
  "current_domain": "infrastructure"
}
```

## Document Management

### POST /upload
Upload documents for analysis.

**Request:** `multipart/form-data`
- `target_documents[]`: Target company files
- `buyer_documents[]`: Buyer company files (optional)
- `target_name`: Target company name
- `buyer_name`: Buyer company name (optional)

**Response:** Redirects to dashboard

### GET /api/documents
List all registered documents.

**Response:**
```json
{
  "documents": [
    {
      "doc_id": "uuid",
      "filename": "contract.pdf",
      "entity": "target",
      "authority_level": 1,
      "status": "processed"
    }
  ],
  "stats": {
    "total": 10,
    "by_entity": {"target": 8, "buyer": 2}
  }
}
```

### GET /api/documents/store
Get document store statistics.

**Query params:** `entity`, `authority`

**Response:**
```json
{
  "total": 10,
  "by_entity": {"target": 8, "buyer": 2},
  "documents": [...]
}
```

## Analysis

### POST /api/analysis/start
Start analysis on uploaded documents.

**Request:**
```json
{
  "domains": ["infrastructure", "network", "cybersecurity"],
  "target_name": "Acme Corp",
  "buyer_name": "BigCo Inc"
}
```

**Response:**
```json
{
  "status": "started",
  "task_id": "task-uuid"
}
```

### GET /api/analysis/status
Get analysis progress.

**Response:**
```json
{
  "status": "running",
  "progress": 65,
  "phase": "reasoning",
  "domains_complete": ["infrastructure", "network"],
  "current_domain": "cybersecurity"
}
```

### POST /api/analysis/stop
Stop running analysis.

## Facts

### GET /api/facts
Get all extracted facts.

**Query params:** `domain`, `category`, `entity`, `status`

**Response:**
```json
{
  "facts": [
    {
      "fact_id": "F-INFRA-001",
      "domain": "infrastructure",
      "category": "hosting",
      "item": "AWS EC2 Instances",
      "details": {"count": 50},
      "evidence": {"exact_quote": "..."},
      "confidence_score": 0.85
    }
  ],
  "count": 150
}
```

### GET /api/facts/{domain}
Get facts for a specific domain.

### GET /api/facts/{fact_id}
Get a specific fact by ID.

### PUT /api/facts/{fact_id}
Update a fact (human correction).

**Request:**
```json
{
  "item": "Updated description",
  "details": {"count": 55}
}
```

## Findings

### GET /api/findings
Get all findings (risks, work items, recommendations).

**Query params:** `type`, `domain`, `severity`

**Response:**
```json
{
  "findings": [
    {
      "finding_id": "R-001",
      "type": "risk",
      "domain": "cybersecurity",
      "title": "Outdated firewall firmware",
      "severity": "high",
      "based_on_facts": ["F-CYBER-005"]
    }
  ]
}
```

### GET /api/risks
Get risks only.

### GET /api/work-items
Get work items only.

## Runs

### GET /api/runs
List all analysis runs.

**Response:**
```json
{
  "runs": [
    {
      "run_id": "2026-01-28_143052_acme",
      "target_name": "Acme Corp",
      "status": "completed",
      "facts_count": 150,
      "risks_count": 25
    }
  ]
}
```

### GET /api/runs/{run_id}
Get specific run details.

### GET /api/runs/{run_id}/facts
Get facts from a specific run.

### GET /api/runs/{run_id}/findings
Get findings from a specific run.

### POST /api/runs/{run_id}/archive
Archive a run.

## Exports

### GET /api/export
Export analysis results.

**Query params:**
- `format`: excel, markdown, csv, json, html
- `type`: applications, infrastructure, risks, all

**Response:** File download

### POST /api/export/generate
Generate exports for current run.

**Request:**
```json
{
  "formats": ["excel", "markdown"],
  "types": ["applications", "risks"]
}
```

## Inventory

### GET /api/inventory/{domain}
Get inventory for a domain.

**Domains:** applications, infrastructure, network, cybersecurity, identity, organization

**Response:**
```json
{
  "items": [
    {
      "name": "SAP S/4HANA",
      "category": "ERP",
      "vendor": "SAP",
      "status": "active",
      "facts": ["F-APP-001", "F-APP-002"]
    }
  ]
}
```

### GET /api/inventory/{domain}/{item_id}/dossier
Get evidence dossier for an inventory item.

## Sessions

### GET /api/session
Get current session info.

### DELETE /api/session
Clear current session.

## Error Responses

All errors return:
```json
{
  "status": "error",
  "message": "Description of the error",
  "code": "ERROR_CODE"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad request
- `404`: Not found
- `500`: Server error

## Rate Limiting

Production deployments enforce rate limits:
- 100 requests/minute per IP
- 10 concurrent analysis tasks

## Authentication (Production)

When authentication is enabled:
```
Authorization: Bearer <token>
```

See also:
- [Architecture Overview](architecture.md)
- [Data Flow](data-flow.md)
- [Deployment Guide](deployment.md)
