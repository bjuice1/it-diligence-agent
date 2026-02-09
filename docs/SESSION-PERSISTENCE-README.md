# Session Persistence Fix - Documentation Index

## 📚 Documentation Overview

This directory contains comprehensive documentation for the Session Persistence implementation (Specs 01-04).

---

## 🎯 Choose Your Documentation

### Quick Reference Guide (⚡ Start Here for Troubleshooting)
**File:** [SESSION-PERSISTENCE-QUICKREF.md](./SESSION-PERSISTENCE-QUICKREF.md)

**Use this when:**
- ✅ Need to debug an issue quickly
- ✅ Looking for specific command or query
- ✅ Want to check configuration
- ✅ Need emergency fixes

**Contents:**
- Emergency troubleshooting checklist
- Debug commands (copy-paste ready)
- Common fixes with commands
- Health check procedures
- Performance benchmarks

**Time to solution:** 2-5 minutes

---

### Full Technical Documentation (📖 Comprehensive Reference)
**File:** [SESSION-PERSISTENCE-IMPLEMENTATION.md](./SESSION-PERSISTENCE-IMPLEMENTATION.md)

**Use this when:**
- ✅ Need to understand the architecture
- ✅ Want to trace through code logic
- ✅ Debugging complex issues
- ✅ Adding new features
- ✅ Onboarding new developers

**Contents:**
- Complete architecture diagrams with line numbers
- Detailed data flow with decision trees
- Component reference with code traces
- Comprehensive debugging guide
- Database schema with migrations
- Full API reference
- Testing procedures
- Maintenance guides

**Time to read:** 30-60 minutes

---

### Specification Documents (📋 Original Design)
**Directory:** [../specs/session-persistence-fix/](../specs/session-persistence-fix/)

**Use this when:**
- ✅ Need to understand original requirements
- ✅ Want to see what was planned vs implemented
- ✅ Looking for test criteria
- ✅ Need implementation notes

**Files:**
1. `00-implementation-guide.md` - Build manifest
2. `01-user-deal-association-schema.md` - Database schema spec
3. `02-deal-selection-api.md` - API endpoint spec
4. `03-automatic-context-restoration.md` - Auto-restore hook spec
5. `04-session-architecture-hardening.md` - Session backend spec

---

## 🚀 Quick Start Paths

### Path 1: "Something is broken, fix it now!"
```
1. Open: SESSION-PERSISTENCE-QUICKREF.md
2. Go to: 🚨 Emergency Troubleshooting
3. Run the Quick Checks commands
4. Apply the most common fix
5. If not fixed → Check Full Technical Documentation
```

### Path 2: "I need to understand how this works"
```
1. Read: SESSION-PERSISTENCE-IMPLEMENTATION.md
   - Start with: Architecture Overview
   - Then: Data Flow & Logic
   - Deep dive: Component Reference

2. Trace code:
   - Use line numbers provided
   - Follow execution paths in diagrams
   - Reference debugging guide as needed
```

### Path 3: "I'm adding a new feature"
```
1. Review: Spec documents (original design)
2. Understand: SESSION-PERSISTENCE-IMPLEMENTATION.md
   - Focus on: Component Reference
   - Check: Integration points
   - Review: Testing procedures

3. Extend:
   - Follow existing patterns
   - Add tests (see Testing section)
   - Update documentation
```

### Path 4: "I'm onboarding to this codebase"
```
1. Read in order:
   a. This file (you are here)
   b. SESSION-PERSISTENCE-IMPLEMENTATION.md
      - Architecture Overview (15 min)
      - Data Flow & Logic (20 min)
   c. SESSION-PERSISTENCE-QUICKREF.md
      - Skim for reference

2. Hands-on:
   - Run debug commands from Quick Ref
   - Trace a request through the code
   - Test auto-restore manually
   - Review test coverage
```

---

## 🔍 Finding Specific Information

### "Where is the code for X?"
→ **SESSION-PERSISTENCE-IMPLEMENTATION.md** → **Component Reference** → Find table with file locations

### "How do I debug Y?"
→ **SESSION-PERSISTENCE-QUICKREF.md** → **Debug Commands** or **🚨 Emergency Troubleshooting**

### "What queries does Z run?"
→ **SESSION-PERSISTENCE-IMPLEMENTATION.md** → **Data Flow & Logic** → Look for query traces

### "How do I configure W?"
→ **SESSION-PERSISTENCE-QUICKREF.md** → **Configuration Quick Reference**

### "What's the SQL for migration V?"
→ **SESSION-PERSISTENCE-IMPLEMENTATION.md** → **Database Schema** → Complete Schema Changes

### "How do I test feature U?"
→ **SESSION-PERSISTENCE-IMPLEMENTATION.md** → **Testing & Verification** → Find test scenario

### "What happens when T?"
→ **SESSION-PERSISTENCE-IMPLEMENTATION.md** → **Data Flow & Logic** → Find decision tree

---

## 📊 Implementation Summary

### What Was Built

| Spec | Component | Files Modified | Lines Added | Tests |
|------|-----------|----------------|-------------|-------|
| 01 | User-Deal Schema | database.py | +70 | 7 |
| 02 | Deal Selection API | permissions.py (NEW), app.py | +265 | 10 |
| 03 | Auto-Restore Hook | app.py | +65 | 8 |
| 04 | Session Hardening | app.py, database.py, maintenance_tasks.py (NEW) | +400 | 5 |
| **Total** | **4 Specs** | **4 files** | **+800 lines** | **30** |

### Key Features

✅ **Persistent Deal Selection**
- Survives browser restarts, session expiry, server restarts
- Database-backed with `User.last_deal_id`

✅ **Automatic Restoration**
- Zero user friction - deal context auto-restored
- Runs on every request, <1ms overhead for warm sessions

✅ **Multi-Server Ready**
- Works with load balancers
- Redis or SQLAlchemy session backend
- Database is source of truth

✅ **Production Hardened**
- Health monitoring endpoints
- Session cleanup tasks
- Permission-based access control
- Comprehensive error handling

---

## 🎯 Common Use Cases

### Use Case 1: User Reports "Lost My Deal Selection"

**Documentation Path:**
1. **Quick Ref** → Emergency Troubleshooting → Issue: Users Losing Deal Selection
2. Run the 4 quick checks
3. Most likely: User selected deal via old method
4. Fix: User re-selects via `POST /api/deals/<id>/select`

**Time to resolution:** 5 minutes

---

### Use Case 2: High Database Load After Deployment

**Documentation Path:**
1. **Quick Ref** → Emergency Troubleshooting → Issue: High Database Load
2. Check if early exit is working (should be 99% of requests)
3. **Full Docs** → Debugging Guide → Performance Profiling
4. Add monitoring to identify bottleneck

**Time to resolution:** 15-30 minutes

---

### Use Case 3: Session Backend Failing Health Checks

**Documentation Path:**
1. **Quick Ref** → Health Check Commands → Quick Health Check
2. Identify which backend (Redis or SQLAlchemy)
3. **Quick Ref** → Emergency Troubleshooting → Issue: Session Backend Unhealthy
4. Follow backend-specific fix

**Time to resolution:** 10 minutes

---

### Use Case 4: Understanding Permission Logic

**Documentation Path:**
1. **Full Docs** → Data Flow & Logic → Permission Check Logic
2. See complete decision tree with all rules
3. **Full Docs** → Component Reference → Permission Helpers
4. Review code with line numbers

**Time to understand:** 20 minutes

---

### Use Case 5: Adding Audit Logging

**Documentation Path:**
1. **Full Docs** → Component Reference → Deal Selection API
2. See existing audit logging code (lines 4005-4018)
3. **Full Docs** → Data Flow & Logic → Deal Selection Flow
4. Follow the pattern for new endpoints

**Time to implement:** 30 minutes

---

## 📈 Metrics to Monitor

### Production Health Indicators

| Metric | Target | Alert If | Check Via |
|--------|--------|----------|-----------|
| Session backend health | healthy | unhealthy >5min | GET /api/health/session |
| Auto-restore success rate | >95% | <90% | Log analysis |
| Auto-restore latency (p99) | <10ms | >50ms | Performance profiling |
| Deal selection errors | <1% | >5% | Error logs |
| Session table size | <10x users | >100x users | SQL query |

**Monitoring Setup:**
See **Full Docs** → **Troubleshooting** → **Monitoring & Alerts**

---

## 🛠 Maintenance Schedule

### Daily
- **3:00 AM:** Session cleanup task
  - Removes expired sessions from flask_sessions table
  - **Doc:** Quick Ref → Common Fixes → Fix 4

### Weekly
- **Sunday 2:00 AM:** Stale deal reference cleanup
  - Clears last_deal_id for users with deleted deals
  - **Doc:** Quick Ref → Common Fixes → Fix 3

### Continuous
- **Every 5 min:** Health monitoring
  - Check session backend health
  - **Doc:** Quick Ref → Health Check Commands

---

## 🔐 Security Considerations

### Permission Checks
- All deal access goes through `user_can_access_deal()`
- Checks ownership, multi-tenancy, soft-delete
- **Doc:** Full Docs → Component Reference → Permission Check Logic

### Audit Logging
- All deal selections logged (if enabled)
- Includes user ID, deal ID, timestamp
- **Doc:** Full Docs → Data Flow & Logic → Deal Selection Flow → Step 9

### Session Security
- Sessions signed (HMAC)
- Configurable timeout (default: 24 hours)
- HTTPS-only cookies in production
- **Doc:** Full Docs → Session Backend

---

## 📝 Change Log

### Version 1.0.0 (2026-02-09)
- ✅ Initial implementation of Specs 01-04
- ✅ 30/30 tests passing
- ✅ Production deployment ready
- ✅ Documentation complete

---

## 🤝 Contributing

### Before Making Changes

1. **Read:** Relevant spec document
2. **Understand:** Current implementation via Full Docs
3. **Test:** Run existing tests
4. **Add:** New tests for your changes
5. **Update:** Documentation in all 3 files

### Testing Changes

```bash
# Run all session persistence tests
pytest tests/test_session_persistence.py -v

# Test specific component
pytest tests/test_session_persistence.py::test_auto_restore -v

# Manual testing
python3 -c "from test_scripts import test_session_persistence; test_session_persistence()"
```

---

## 💡 Tips for Success

### For Developers
1. **Start with Quick Ref** for fast answers
2. **Use Full Docs** for understanding architecture
3. **Follow the line numbers** - they're accurate
4. **Run the debug commands** - they're tested
5. **Check the decision trees** - they show all paths

### For Operators
1. **Bookmark the health endpoint** - `/api/health/session`
2. **Set up monitoring** using the metrics guide
3. **Schedule cleanup tasks** per maintenance schedule
4. **Know the rollback procedures** (Quick Ref → Common Fixes)
5. **Keep logs accessible** - you'll need them for debugging

### For Architects
1. **Review the architecture diagrams** - they show all layers
2. **Understand the dual persistence** - session + database
3. **Know the performance characteristics** - benchmarks provided
4. **Plan for scale** - multi-server considerations documented
5. **Consider extensions** - patterns are established

---

## 🎓 Learning Path

### Beginner (Just Deployed)
**Time: 30 minutes**
1. Read this file completely
2. Skim Quick Ref for commands
3. Test health endpoint
4. Try one debug command

### Intermediate (Using Daily)
**Time: 2 hours**
1. Read Full Docs: Architecture + Data Flow
2. Trace one request through code
3. Run all debug commands
4. Set up monitoring

### Advanced (Contributing)
**Time: 4 hours**
1. Read all spec documents
2. Read Full Docs completely
3. Trace all execution paths
4. Run all tests
5. Add a new feature

---

## 📞 Getting Help

### Self-Service (Fastest)

1. **Quick Ref** → Emergency Troubleshooting
2. **Full Docs** → Debugging Guide
3. **Specs** → Original requirements

### Need More Help?

**Include in your report:**
- What you tried (from Quick Ref)
- Error messages (exact text)
- Environment (dev/staging/prod)
- Session backend type (from health endpoint)
- Relevant log snippets

**Helpful commands to run:**
```bash
# System info
curl http://localhost:5001/api/health/session | jq
python3 -c "from web.database import User; u = User.query.first(); print(f'last_deal_id: {u.last_deal_id}')"
grep -A 5 "Auto-restore" logs/app.log | tail -20

# Include output of these in your report
```

---

## 🗂 File Organization

```
docs/
├── SESSION-PERSISTENCE-README.md          ← You are here
├── SESSION-PERSISTENCE-QUICKREF.md        ← Quick troubleshooting
└── SESSION-PERSISTENCE-IMPLEMENTATION.md  ← Full technical docs

specs/session-persistence-fix/
├── 00-implementation-guide.md             ← Build manifest
├── 01-user-deal-association-schema.md     ← Spec 01
├── 02-deal-selection-api.md               ← Spec 02
├── 03-automatic-context-restoration.md    ← Spec 03
└── 04-session-architecture-hardening.md   ← Spec 04

web/
├── app.py                                 ← Auto-restore hook, API endpoints, session config
├── database.py                            ← User model, migrations
├── permissions.py                         ← Permission checks (NEW)
└── tasks/
    └── maintenance_tasks.py               ← Cleanup tasks (NEW)
```

---

## ✅ Checklist for New Team Members

**Day 1:**
- [ ] Read this README
- [ ] Skim Quick Reference
- [ ] Test health endpoint locally
- [ ] Run one debug command

**Week 1:**
- [ ] Read Full Documentation (Architecture + Data Flow sections)
- [ ] Trace auto-restore through code
- [ ] Understand permission logic
- [ ] Review test coverage

**Month 1:**
- [ ] Read all spec documents
- [ ] Add a small feature
- [ ] Debug a real issue
- [ ] Update documentation for your changes

---

## 🎉 Success Metrics

**You know you're successful when:**
- ✅ Can debug "lost deal selection" in <5 minutes
- ✅ Can explain auto-restore flow from memory
- ✅ Can add new permission rules confidently
- ✅ Can optimize performance using the guides
- ✅ Can troubleshoot session backend issues independently

---

## 📚 Related Resources

- [Flask-Session Docs](https://flask-session.readthedocs.io/)
- [SQLAlchemy Relationships](https://docs.sqlalchemy.org/en/14/orm/relationships.html)
- [Redis Documentation](https://redis.io/documentation)
- [PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)

---

**Documentation Version:** 1.0.0
**Last Updated:** 2026-02-09
**Status:** ✅ Production Ready
**Total Pages:** 3 docs, ~150KB of content
