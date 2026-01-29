# Phase 4: Polish & Verify - 115-Point Plan

*Created: 2026-01-28*
*Updated: 2026-01-28 (v2 - Added improvements)*
*Status: Planning*
*Depends On: Phase 1, 2, 3*

## Overview

End-to-end testing, performance optimization, security hardening, Docker production setup, and deployment to cloud. Ensures the complete deal lifecycle works reliably, securely, and is ready for real use. Includes user documentation and operational procedures.

---

## Phase A: End-to-End Testing (Points 1-30)
**Status: Not Started**

### Test Infrastructure (1-10)
- [ ] 1. Create `tests/e2e/` directory structure
- [ ] 2. Add `pytest-asyncio` to requirements.txt
- [ ] 3. Add `factory_boy` for test data generation
- [ ] 4. Create `tests/conftest.py` with shared fixtures
- [ ] 5. Create test database configuration (isolated test DB)
- [ ] 6. Create `tests/factories/user_factory.py`
- [ ] 7. Create `tests/factories/deal_factory.py`
- [ ] 8. Create `tests/factories/document_factory.py`
- [ ] 9. Create sample test documents (small PDF, XLSX, DOCX)
- [ ] 10. Set up GitHub Actions CI configuration

### User Flow Tests (11-22)
- [ ] 11. Test: User registration with validation
- [ ] 12. Test: User login/logout with session persistence
- [ ] 13. Test: Create new deal with all fields
- [ ] 14. Test: Upload single document
- [ ] 15. Test: Upload multiple documents batch
- [ ] 16. Test: Run full analysis on deal
- [ ] 17. Test: View dashboard with results
- [ ] 18. Test: View each inventory page (apps, infra, org, cyber)
- [ ] 19. Test: Switch between multiple deals
- [ ] 20. Test: Add documents to existing deal
- [ ] 21. Test: Incremental analysis with merge
- [ ] 22. Test: Export deal data (JSON, Excel)

### Data Integrity Tests (23-30)
- [ ] 23. Test: Facts persist across server restart
- [ ] 24. Test: Deal isolation - user A cannot see user B's deals
- [ ] 25. Test: Document hash prevents duplicate uploads
- [ ] 26. Test: Analysis run creates proper records
- [ ] 27. Test: Rollback restores previous state correctly
- [ ] 28. Test: Concurrent analysis on different deals doesn't interfere
- [ ] 29. Test: Large document handling (100+ page PDF)
- [ ] 30. Test: Unicode and special characters in facts preserved

---

## Phase B: Security Audit (Points 31-50)
**Status: Not Started**

### Authentication & Authorization (31-38)
- [ ] 31. Verify all routes require authentication (except public endpoints)
- [ ] 32. Test: User cannot access another user's deals via API
- [ ] 33. Test: User cannot access another user's documents
- [ ] 34. Test: Admin role has elevated permissions
- [ ] 35. Test: Session expires after configured timeout
- [ ] 36. Test: Password reset flow works securely
- [ ] 37. Implement account lockout after failed login attempts
- [ ] 38. Add security headers (CSP, X-Frame-Options, etc.)

### Input Validation & Injection Prevention (39-45)
- [ ] 39. Test: SQL injection prevented on all endpoints
- [ ] 40. Test: XSS prevented in all user inputs
- [ ] 41. Test: File upload validates type and size
- [ ] 42. Test: Path traversal prevented in file operations
- [ ] 43. Test: CSRF tokens validated on all POST/PATCH/DELETE
- [ ] 44. Sanitize all user input before storage
- [ ] 45. Validate and sanitize document filenames

### Secrets & Data Protection (46-50)
- [ ] 46. Audit: No secrets in code or logs
- [ ] 47. Audit: API keys not exposed in frontend
- [ ] 48. Audit: Passwords properly hashed (bcrypt)
- [ ] 49. Implement API key rotation capability
- [ ] 50. Add data encryption at rest option (future)

---

## Phase C: Performance Optimization (Points 51-70)
**Status: Not Started**

### Database Optimization (51-58)
- [ ] 51. Enable query logging and identify slow queries
- [ ] 52. Fix N+1 query problems with eager loading
- [ ] 53. Add missing indexes based on query analysis
- [ ] 54. Implement query result caching with Redis (TTL-based)
- [ ] 55. Optimize dashboard summary queries
- [ ] 56. Add database connection pool tuning
- [ ] 57. Create `scripts/db_maintenance.py` (VACUUM, ANALYZE)
- [ ] 58. Add query timeout limits (30s default)

### API & Response Optimization (59-65)
- [ ] 59. Enable gzip response compression
- [ ] 60. Add ETags for conditional requests
- [ ] 61. Implement pagination on all list endpoints
- [ ] 62. Add API response caching headers
- [ ] 63. Profile and optimize slow endpoints
- [ ] 64. Add request timing middleware (log slow requests)
- [ ] 65. Optimize JSON serialization

### Frontend Optimization (66-70)
- [ ] 66. Minify CSS and JavaScript for production
- [ ] 67. Add cache headers for static files (1 year)
- [ ] 68. Implement lazy loading for large tables
- [ ] 69. Add loading skeletons/spinners for async data
- [ ] 70. Reduce initial page payload size

---

## Phase D: Error Handling & Monitoring (Points 71-90)
**Status: Not Started**

### Error Handling (71-78)
- [ ] 71. Implement global exception handler with logging
- [ ] 72. Create structured error response format (JSON)
- [ ] 73. Add user-friendly error pages (400, 401, 403, 404, 500)
- [ ] 74. Implement retry logic for Anthropic API failures
- [ ] 75. Add circuit breaker for external API calls
- [ ] 76. Handle database connection failures gracefully
- [ ] 77. Handle Redis connection failures (fallback to memory)
- [ ] 78. Create error recovery documentation

### Logging & Observability (79-85)
- [ ] 79. Implement structured logging (JSON format)
- [ ] 80. Add request ID to all log entries (correlation)
- [ ] 81. Add user_id and deal_id context to logs
- [ ] 82. Configure log levels (DEBUG, INFO, WARN, ERROR)
- [ ] 83. Add performance metrics logging (response times)
- [ ] 84. Implement log rotation (daily, keep 30 days)
- [ ] 85. Create `/metrics` endpoint for monitoring

### Health Checks & Monitoring (86-90)
- [ ] 86. Enhance `/health` with dependency status (DB, Redis, Celery)
- [ ] 87. Add `/health/ready` for Kubernetes readiness
- [ ] 88. Add `/health/live` for liveness probe
- [ ] 89. Document monitoring thresholds and alerts
- [ ] 90. Create operations runbook for common issues

---

## Phase E: Docker Production Setup (Points 91-105)
**Status: Not Started**

### Dockerfile Optimization (91-97)
- [ ] 91. Use multi-stage build (builder + runtime)
- [ ] 92. Minimize image size (slim base, remove dev deps)
- [ ] 93. Run as non-root user for security
- [ ] 94. Configure proper signal handling (SIGTERM)
- [ ] 95. Add HEALTHCHECK instruction
- [ ] 96. Create `.dockerignore` for build optimization
- [ ] 97. Pin all base image versions

### Docker Compose Production (98-105)
- [ ] 98. Create `docker/docker-compose.prod.yml`
- [ ] 99. Configure PostgreSQL with persistent volume and backups
- [ ] 100. Configure Redis with AOF persistence
- [ ] 101. Add Nginx reverse proxy with SSL termination
- [ ] 102. Configure automatic database backups (daily)
- [ ] 103. Add resource limits (memory, CPU per service)
- [ ] 104. Configure restart policies (always for services)
- [ ] 105. Use Docker secrets for sensitive values

---

## Phase F: Cloud Deployment & Documentation (Points 106-115)
**Status: Not Started**

### Railway Deployment (106-110)
- [ ] 106. Create `railway.json` with build configuration
- [ ] 107. Configure Railway PostgreSQL and Redis addons
- [ ] 108. Set up environment variables securely
- [ ] 109. Configure custom domain with SSL
- [ ] 110. Test deployment and rollback procedures

### Documentation (111-115)
- [ ] 111. Create user guide: Getting Started
- [ ] 112. Create user guide: Deal Management
- [ ] 113. Create user guide: Document Upload & Analysis
- [ ] 114. Create operations runbook: Backup & Restore
- [ ] 115. Create operations runbook: Troubleshooting

---

## File Changes Summary

### New Files
| File | Purpose |
|------|---------|
| `tests/e2e/test_user_flows.py` | E2E user flow tests |
| `tests/e2e/test_data_integrity.py` | Data integrity tests |
| `tests/e2e/test_security.py` | Security tests |
| `tests/factories/*.py` | Test data factories |
| `tests/conftest.py` | Pytest fixtures |
| `.github/workflows/test.yml` | CI configuration |
| `docker/docker-compose.prod.yml` | Production compose |
| `docker/nginx.conf` | Nginx configuration |
| `scripts/db_maintenance.py` | Database maintenance |
| `scripts/backup_db.py` | Database backup |
| `scripts/restore_db.py` | Database restore |
| `docs/user-guide/getting-started.md` | User documentation |
| `docs/user-guide/deal-management.md` | User documentation |
| `docs/user-guide/analysis.md` | User documentation |
| `docs/operations/runbook.md` | Operations runbook |
| `docs/operations/backup-restore.md` | Backup procedures |
| `docs/operations/troubleshooting.md` | Troubleshooting guide |

### Modified Files
| File | Changes |
|------|---------|
| `docker/Dockerfile` | Multi-stage, optimized, non-root |
| `docker/.dockerignore` | Build optimization |
| `web/app.py` | Add metrics, improve error handling |
| `config_v2.py` | Production configuration |
| `requirements.txt` | Add test dependencies |

---

## Test Coverage Targets

| Area | Target | Notes |
|------|--------|-------|
| Database Models | 90% | All CRUD operations |
| Repositories | 85% | Query methods |
| Services | 80% | Business logic |
| API Endpoints | 75% | Request/response |
| E2E Critical Paths | 100% | User workflows |

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Dashboard load | < 2s | Time to interactive |
| API list response | < 500ms | 95th percentile |
| API detail response | < 200ms | 95th percentile |
| Document upload | < 10s | Per 10MB file |
| Analysis start | < 5s | Time to first progress |
| Concurrent users | 20+ | Without degradation |

---

## Security Checklist

### Authentication
- [ ] All sensitive routes require login
- [ ] Password minimum 8 chars with complexity
- [ ] Account lockout after 5 failed attempts
- [ ] Session timeout enforced (7 days)
- [ ] Secure session cookies (HttpOnly, Secure, SameSite)

### Authorization
- [ ] Users can only access own deals
- [ ] Admin role properly restricted
- [ ] API endpoints check ownership

### Data Protection
- [ ] HTTPS enforced (redirect HTTP)
- [ ] CSRF tokens on all forms
- [ ] XSS prevented (template escaping)
- [ ] SQL injection prevented (parameterized)
- [ ] File upload restrictions enforced

### Secrets
- [ ] No secrets in code
- [ ] No secrets in logs
- [ ] Environment variables for config
- [ ] Docker secrets for production

---

## Accessibility Checklist (WCAG 2.1 AA)

- [ ] All images have alt text
- [ ] Color contrast meets 4.5:1 ratio
- [ ] Forms have proper labels
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Error messages are descriptive
- [ ] Page has proper heading hierarchy

---

## Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest 2 | Required |
| Firefox | Latest 2 | Required |
| Safari | Latest 2 | Required |
| Edge | Latest 2 | Required |
| IE 11 | - | Not Supported |

---

## Disaster Recovery

### Backup Schedule
- Database: Daily at 2 AM UTC, retain 30 days
- Documents: Replicated storage, 3 copies
- Configuration: Version controlled in git

### Recovery Targets
- RTO (Recovery Time Objective): 4 hours
- RPO (Recovery Point Objective): 24 hours

### Recovery Procedures
1. Restore database from latest backup
2. Restore documents from replicated storage
3. Deploy application from git
4. Verify health checks pass
5. Notify users of recovery

---

## Progress Summary

| Phase | Points | Complete | Status |
|-------|--------|----------|--------|
| A: End-to-End Testing | 1-30 | 0/30 | Not Started |
| B: Security Audit | 31-50 | 0/20 | Not Started |
| C: Performance Optimization | 51-70 | 0/20 | Not Started |
| D: Error Handling & Monitoring | 71-90 | 0/20 | Not Started |
| E: Docker Production | 91-105 | 0/15 | Not Started |
| F: Deployment & Documentation | 106-115 | 0/10 | Not Started |

**Overall: 0/115 points complete (0%)**

---

## Success Criteria

Phase 4 is complete when:
1. All E2E tests pass
2. Security audit complete with no critical issues
3. Performance meets all targets
4. Error handling is robust with proper recovery
5. Docker production setup works locally
6. Successfully deployed to Railway
7. All user and operations documentation complete
8. Backup and restore tested and documented

---

## Definition of Done (Overall Project)

The infrastructure foundation is complete when a user can:

1. **Create an account and log in**
2. **Create a new deal with target/buyer info**
3. **Upload documents (PDF, XLSX, DOCX)**
4. **Run analysis and see progress**
5. **View results across all domains**
6. **Review and verify facts**
7. **Export reports and data**
8. **Create another deal and switch between them**
9. **Add more documents and update analysis**
10. **See what changed since last review**

And operationally:
- Data persists reliably
- Each user sees only their data
- System recovers from failures
- Performance is acceptable
- Security is enforced

At this point, iterate on:
- Analysis quality and prompts
- Report formatting and language
- Domain-specific logic
- Export templates
- UI polish

---

## Notes

- Security audit includes OWASP Top 10 checks
- Accessibility ensures usability for all users
- Browser testing covers 95%+ of users
- Disaster recovery tested quarterly
- Documentation written for end users, not just developers
