# Spec 05-MVP: Explanatory UI Enhancement (2-Week Version)
**Version:** MVP 1.0
**Date:** February 10, 2026
**Status:** Ready for Implementation
**Estimated Effort:** 2 weeks (AI-assisted solo development)

---

## What This MVP Does

Surfaces existing backend depth (reasoning, cost breakdowns) in the UI **using data you already have**. No new data models, no backend changes, just better presentation.

**User Complaints Addressed:**
- ✅ "Outputs too surface level" → Show reasoning inline
- ✅ "Show calculations" → Add "View Calculation" button
- ✅ "Explain why not just what" → Surface existing `reasoning` field

**What's Deferred to v2:**
- ❌ ResourceBuildUp display (Spec 01 not built yet)
- ❌ Hierarchical drill-down (Spec 04 not built yet)
- ❌ Source facts panel (nice-to-have)
- ❌ ConfidenceBadge component (nice-to-have)

---

## Implementation Plan (2 Weeks)

### Week 1: Core UI Components

**Day 1-2: FindingCard with Inline Context**
```jsx
// Minimal version - just show reasoning if it exists
const FindingCard = ({ finding }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className="finding-card">
      <Card.Body>
        {/* Existing: Title + severity */}
        <h5>{finding.title}</h5>
        <Badge bg={getSeverityColor(finding.severity)}>{finding.severity}</Badge>

        {/* NEW: Inline reasoning (if exists) */}
        {finding.reasoning && (
          <div className="inline-context">
            💡 {finding.reasoning.split('.')[0] + '.'}
          </div>
        )}

        {/* NEW: Expand button (if more content exists) */}
        {(finding.mna_implication || finding.mitigation) && (
          <Button variant="link" onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Hide Details ▲' : 'Explain This ▼'}
          </Button>
        )}

        {/* NEW: Expanded section */}
        {expanded && (
          <div className="expanded-details">
            {finding.mna_implication && (
              <div>
                <strong>M&A Implications:</strong>
                <p>{finding.mna_implication}</p>
              </div>
            )}
            {finding.mitigation && (
              <div>
                <strong>Mitigation:</strong>
                <p>{finding.mitigation}</p>
              </div>
            )}
          </div>
        )}
      </Card.Body>
    </Card>
  );
};
```

**Day 3: Basic CSS Styling**
```css
.inline-context {
  padding: 12px;
  background: #f6f8fa;
  border-left: 3px solid #0969da;
  margin: 12px 0;
}

.expanded-details {
  margin-top: 16px;
  padding: 16px;
  background: #f6f8fa;
  border-radius: 6px;
}
```

**Day 4-5: Cost Breakdown Modal**
```jsx
const CostBreakdownModal = ({ finding, onClose }) => {
  const cost = finding.cost_buildup_json; // Assumes CostBuildUp exists

  if (!cost) return null;

  return (
    <Modal show={true} onHide={onClose}>
      <Modal.Header closeButton>
        <Modal.Title>Cost Breakdown</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <h5>Total: ${cost.cost_low?.toLocaleString()} - ${cost.cost_high?.toLocaleString()}</h5>

        {/* Simple list of assumptions */}
        {cost.assumptions && cost.assumptions.length > 0 && (
          <div>
            <h6>Assumptions:</h6>
            <ul>
              {cost.assumptions.map((a, i) => <li key={i}>{a}</li>)}
            </ul>
          </div>
        )}

        {/* Show cost components if they exist */}
        {cost.cost_components && cost.cost_components.length > 0 && (
          <div>
            <h6>Breakdown:</h6>
            {cost.cost_components.map((comp, i) => (
              <div key={i}>
                {comp.label}: ${comp.cost_low?.toLocaleString()}
              </div>
            ))}
          </div>
        )}
      </Modal.Body>
    </Modal>
  );
};
```

---

### Week 2: Integration & Polish

**Day 6-7: Wire Up API Endpoints**
```python
# web/api/findings.py (enhance existing endpoint)

@findings_api.route('/api/findings/<finding_id>', methods=['GET'])
def get_finding(finding_id):
    finding = Finding.query.get_or_404(finding_id)

    return jsonify({
        "id": finding.id,
        "title": finding.title,
        "severity": finding.severity,
        "reasoning": finding.reasoning,  # ← Already exists
        "mna_implication": finding.mna_implication,  # ← Already exists
        "mitigation": finding.mitigation,  # ← Already exists
        "cost_buildup": finding.cost_buildup_json,  # ← Already exists
        # NEW: Convenience flags
        "has_reasoning": bool(finding.reasoning),
        "has_cost_buildup": finding.cost_buildup_json is not None,
    })
```

**Day 8: Add "View Calculation" Button**
```jsx
// In FindingCard component
{finding.cost_buildup_json && (
  <Button
    variant="link"
    onClick={() => setShowCostModal(true)}
  >
    View Calculation ▶
  </Button>
)}

{showCostModal && (
  <CostBreakdownModal
    finding={finding}
    onClose={() => setShowCostModal(false)}
  />
)}
```

**Day 9: Testing**
- Manual testing: Click through all findings, verify reasoning shows
- Test cost modal: Open/close, verify data displays
- Mobile responsive: Check on phone
- Fix bugs found

**Day 10: Deploy to Railway**
```bash
git add web/static/js/components/FindingCard.jsx
git add web/static/css/explanatory-ui.css
git add web/api/findings.py
git commit -m "Add explanatory UI enhancement (MVP)"
git push origin main
# Railway auto-deploys
```

---

## Success Criteria (MVP)

**Ship when:**
- ✅ Every finding with `reasoning` shows inline context
- ✅ "Explain This" button works for findings with implications
- ✅ "View Calculation" button shows cost breakdown
- ✅ No console errors in browser
- ✅ Works on mobile (basic responsive)

**Defer to v2:**
- Resource breakdown (needs Spec 01)
- Source facts panel (nice-to-have)
- Confidence badges (nice-to-have)
- Advanced drill-down (needs Spec 04)

---

## What You Get for 2 Weeks of Work

**Before:**
```
Finding: Oracle E-Business Suite 11i
[No context visible]
```

**After MVP:**
```
Finding: Oracle E-Business Suite 11i
💡 2 generations behind current version, limiting integration options

[Explain This ▼] [View Calculation ▶]

[If clicked "Explain This":]
M&A Implications:
Post-acquisition, this system will require immediate upgrade
or replacement, impacting separation timeline...

Mitigation:
Plan 18-month ERP modernization in integration roadmap
```

**User value:**
- They can now see WHY findings matter (reasoning visible)
- They can see HOW costs are calculated (assumptions visible)
- They get context without leaving the findings page

**Risk:** Minimal (no schema changes, uses existing data)

---

## Validation Plan

**After deploying MVP, ask users:**
1. "Is this more helpful than before?" (Yes/No/Somewhat)
2. "Do you click 'Explain This' often?" (Never/Sometimes/Often)
3. "Do you need deeper drill-down, or is this enough?" (Need more/This is enough)

**If "This is enough":** Stop here, saved 3 months on Specs 01-04, 06-07
**If "Need more":** Proceed to full Spec 05 (add ResourceBuildUp, hierarchy, etc.)

---

## Files to Create/Modify

**New Files (3):**
1. `web/static/js/components/FindingCard.jsx` (200 lines)
2. `web/static/js/components/CostBreakdownModal.jsx` (100 lines)
3. `web/static/css/explanatory-ui.css` (150 lines)

**Modified Files (1):**
1. `web/api/findings.py` (add `has_*` flags, 10 lines)

**Total:** ~460 lines of code (Claude Code will write 80% of this)

---

## Deployment Checklist

**Pre-Deploy:**
- [ ] Test locally with real deal data
- [ ] Verify all findings with reasoning show inline context
- [ ] Verify cost modal works
- [ ] Check mobile responsive
- [ ] No console errors

**Deploy:**
- [ ] Push to GitHub
- [ ] Railway auto-deploys
- [ ] Check Railway logs for errors
- [ ] Test on production URL

**Post-Deploy:**
- [ ] Send email to users: "New feature: Click 'Explain This' to see why findings matter"
- [ ] Monitor usage (are they clicking the buttons?)
- [ ] Collect feedback (Google Form or email)

---

## Estimated Timeline Breakdown

| Task | Time (AI-Assisted) | Deliverable |
|------|-------------------|-------------|
| FindingCard component | 1 day | Inline reasoning display |
| CSS styling | 0.5 days | Professional look |
| CostBreakdownModal | 1 day | Cost transparency |
| API enhancements | 0.5 days | has_* flags |
| "View Calculation" button | 0.5 days | Wiring |
| Testing | 1 day | Bug-free |
| Deployment | 0.5 days | Live on Railway |
| Buffer | 1 day | Unexpected issues |
| **TOTAL** | **6.5 days** | **Shipped MVP** |

**With full-time focus:** 1.5 weeks
**With part-time (4 hrs/day):** 2.5 weeks
**Conservative estimate:** 2 weeks

---

## Next Steps After MVP Ships

**Scenario A: Users Love It**
- Measure: >60% of users click "Explain This" at least once
- Action: Proceed to full Spec 05 (add ResourceBuildUp display, source facts)

**Scenario B: Users Don't Use It**
- Measure: <20% of users click buttons
- Action: Interview users - why not? Too much info? Wrong info?
- Pivot: Maybe they want different features (cost accuracy, not explanations)

**Scenario C: Users Want More Depth**
- Measure: Users click through to "Explain This" but ask for resource estimates
- Action: Build Spec 01-03 (ResourceBuildUp + Cost Integration)

**The key:** You'll KNOW which scenario you're in after 2 weeks, not guessing for 3 months.

---

**Status:** ✅ Ready to implement
**Risk Level:** 🟢 Low (uses existing data, no schema changes)
**User Value:** 🟢 High (directly addresses feedback)
**Effort:** 🟢 2 weeks

Ship this first. Validate. Then decide on the other 7 specs.
