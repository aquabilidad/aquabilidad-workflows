# Aquabilidad Workflows for CivicStream

This repository contains fishing industry workflows for the Aquabilidad project, implemented as CivicStream plugins.

## Overview

Aquabilidad is a sustainable fishing management system that provides:
- Commercial fishing permit applications
- Daily catch reporting and quota tracking
- Supply chain traceability from boat to consumer
- Blockchain-based transparency

## Workflows

### 1. Fishing Permit Application (`fishing_permit_v1`)
Handles commercial fishing permit applications including vessel verification, safety inspections, quota allocation, and fee processing.

### 2. Catch Reporting (`catch_reporting_v1`)
Enables fishermen to report their daily catch with GPS location, species, quantities, and automatic quota tracking.

### 3. Traceability & Invoice Linking (`traceability_v1`)
Links catch reports to sales invoices, generates QR codes for consumer verification, and records transactions on blockchain.

## Installation

### Using CivicStream Plugin Manager

1. Via API:
```bash
curl -X POST http://localhost:8000/api/v1/plugins/add \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "aquabilidad-workflows",
    "repo_url": "https://github.com/aquabilidad/aquabilidad-workflows"
  }'
```

2. Via Configuration:
Add to your `plugins.yaml`:
```yaml
plugins:
  - name: aquabilidad-workflows
    repo_url: https://github.com/aquabilidad/aquabilidad-workflows
    enabled: true
```

## Development

### Requirements
- Python 3.8+
- CivicStream core dependencies

### Testing
```bash
pip install -r requirements.txt
pytest tests/
```

## License
MIT License - See LICENSE file for details