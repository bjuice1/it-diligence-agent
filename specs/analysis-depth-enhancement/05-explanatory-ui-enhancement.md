# Spec 05: Explanatory UI Enhancement
**Version:** 1.0
**Date:** February 10, 2026
**Status:** Ready for Implementation
**Dependencies:** Specs 01-04 (Data models and hierarchy architecture)

---

## Executive Summary

This specification addresses the **critical UI gap** where rich backend analytical depth exists but isn't prominently displayed to users.

### User Feedback Context

**Original Complaints:**
- "Analysis depth needs more context and explanation with outputs being too surface level"
- "Pulling findings with more thought expansion, additional description, supporting context"
- "Explanations of WHY rather than stating found"
- "Cost tracking visibility - ability to show calculations based on inventory data"

**Root Cause Diagnosis:**
- ✅ Backend HAS excellent depth (reasoning, implications, cost buildup, resource buildup)
- ❌ UI does NOT surface this depth prominently
- ❌ Users see only titles/summaries, miss the rich context hidden in JSON fields
- ❌ No "Explain This" or "View Calculation" UI affordances

**Target State:**
Every finding, fact, and estimate should have:
1. **Inline context** - Key insights visible without clicking
2. **Expand/explain affordances** - "Why this matters", "View calculation", "Show reasoning"
3. **Evidence chains** - Click through to source facts
4. **Calculation transparency** - See formulas, assumptions, sources
5. **Hierarchical drill-down** - Expand to see sub-components

---

## Architecture Overview

### UI Enhancement Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Finding Display                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: SUMMARY (Always visible)                          │
│  ┌────────────────────────────────────────────────────────┐│
│  │ 🔴 High  Legacy ERP System (Oracle E-Business Suite)   ││
│  │         Compatibility and integration risks             ││
│  └────────────────────────────────────────────────────────┘│
│                                                              │
│  Layer 2: INLINE CONTEXT (Key insights, 1-2 lines)         │
│  ┌────────────────────────────────────────────────────────┐│
│  │ 💡 2 generations behind current version, limiting      ││
│  │    integration options and creating technical debt      ││
│  └────────────────────────────────────────────────────────┘│
│                                                              │
│  Layer 3: EXPANDABLE DETAILS (Click to reveal)             │
│  ┌────────────────────────────────────────────────────────┐│
│  │ [Explain This ▼] [View Calculation ▶] [Source Facts ▶] ││
│  │                                                          ││
│  │ [EXPANDED:]                                              ││
│  │                                                          ││
│  │ Why This Matters:                                        ││
│  │ ───────────────                                         ││
│  │ Oracle E-Business Suite 11i is end-of-life (EOL) and   ││
│  │ no longer receives security patches. This creates:      ││
│  │   • Compliance risk (SOX, PCI-DSS require patching)    ││
│  │   • Integration barriers (modern APIs unavailable)      ││
│  │   • Cloud migration blockers (not cloud-compatible)     ││
│  │                                                          ││
│  │ M&A Implications:                                        ││
│  │ ────────────────                                        ││
│  │ Post-acquisition, this system will require:             ││
│  │   • Immediate upgrade ($200k-$300k) OR                  ││
│  │   • Full replacement with modern ERP ($2M-$4M)          ││
│  │   • 18-24 month timeline impacts integration schedule   ││
│  │                                                          ││
│  │ Mitigation Strategy:                                     ││
│  │ ──────────────────                                      ││
│  │ • Phase 1: Assess upgrade vs replace trade-offs        ││
│  │ • Phase 2: Plan ERP modernization in Year 1 roadmap    ││
│  │ • Phase 3: Budget $2.5M-$4M for ERP initiative          ││
│  │                                                          ││
│  │ Source Evidence: [3 facts ▶]                            ││
│  │   F-APP-001: Oracle E-Business Suite 11i in inventory  ││
│  │   F-APP-008: Last patch 2015, EOL confirmed            ││
│  │   F-INT-004: 23 integration endpoints (all SOAP-based)  ││
│  └────────────────────────────────────────────────────────┘│
│                                                              │
│  Layer 4: CALCULATION TRANSPARENCY (Modal/slide-out)        │
│  ┌────────────────────────────────────────────────────────┐│
│  │ [View Calculation modal opened]                         ││
│  │                                                          ││
│  │ ERP Upgrade Cost Breakdown                              ││
│  │ ══════════════════════════                              ││
│  │                                                          ││
│  │ Total: $200,000 - $300,000                              ││
│  │                                                          ││
│  │ Labor Costs ($180k - $270k):                            ││
│  │ ├─ Discovery & Planning: $30k - $40k                    ││
│  │ │  • 2-3 PM × $15k/PM (blended rate)                    ││
│  │ │  • Roles: Solution Architect, ERP Consultant          ││
│  │ ├─ Upgrade Execution: $100k - $150k                     ││
│  │ │  • 8-12 PM × $12.5k/PM                                ││
│  │ │  • Roles: ERP Developer (3), DBA (1), PM (0.5)        ││
│  │ └─ Testing & Validation: $50k - $80k                    ││
│  │    • 4-6 PM × $12.5k/PM                                 ││
│  │    • Roles: QA Engineer (2), Business Analyst (1)       ││
│  │                                                          ││
│  │ Non-Labor Costs ($20k - $30k):                          ││
│  │ └─ Oracle licensing & support: $20k - $30k              ││
│  │                                                          ││
│  │ Assumptions:                                             ││
│  │ • Standard upgrade path (no customizations)             ││
│  │ • Team has Oracle experience                            ││
│  │ • Downtime window available                             ││
│  │                                                          ││
│  │ Source: Gartner 2025 ERP Benchmarks                     ││
│  │ Confidence: Medium (70%) - based on inventory analysis  ││
│  └────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Finding Card with Expandable Context

**Component:** `FindingCard.jsx`

```jsx
import React, { useState } from 'react';
import { Card, Badge, Collapse, Button } from 'react-bootstrap';
import CalculationModal from './CalculationModal';
import SourceFactsPanel from './SourceFactsPanel';

const FindingCard = ({ finding }) => {
  const [expanded, setExpanded] = useState(false);
  const [showCalculation, setShowCalculation] = useState(false);
  const [showSources, setShowSources] = useState(false);

  const hasReasoning = finding.reasoning && finding.reasoning.trim().length > 0;
  const hasImplication = finding.mna_implication && finding.mna_implication.trim().length > 0;
  const hasMitigation = finding.mitigation && finding.mitigation.trim().length > 0;
  const hasCostBuildup = finding.cost_buildup_json !== null;
  const hasResourceBuildup = finding.resource_buildup_json !== null;
  const hasSourceFacts = finding.source_facts && finding.source_facts.length > 0;

  // Extract inline context (first sentence of reasoning)
  const inlineContext = hasReasoning
    ? finding.reasoning.split('.')[0] + '.'
    : null;

  return (
    <Card className="finding-card" data-finding-id={finding.id}>
      {/* Layer 1: Summary */}
      <Card.Body>
        <div className="finding-header">
          <Badge
            bg={finding.severity === 'high' ? 'danger' : finding.severity === 'medium' ? 'warning' : 'info'}
          >
            {finding.severity.toUpperCase()}
          </Badge>
          <h5 className="finding-title">{finding.title}</h5>
        </div>

        {/* Layer 2: Inline Context */}
        {inlineContext && (
          <div className="finding-inline-context">
            <span className="context-icon">💡</span>
            <span className="context-text">{inlineContext}</span>
          </div>
        )}

        {/* Layer 3: Affordances */}
        <div className="finding-actions">
          {(hasReasoning || hasImplication || hasMitigation) && (
            <Button
              variant="link"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Hide Details ▲' : 'Explain This ▼'}
            </Button>
          )}

          {(hasCostBuildup || hasResourceBuildup) && (
            <Button
              variant="link"
              size="sm"
              onClick={() => setShowCalculation(true)}
            >
              View Calculation ▶
            </Button>
          )}

          {hasSourceFacts && (
            <Button
              variant="link"
              size="sm"
              onClick={() => setShowSources(!showSources)}
            >
              Source Facts ({finding.source_facts.length}) ▶
            </Button>
          )}
        </div>

        {/* Layer 3: Expanded Details */}
        <Collapse in={expanded}>
          <div className="finding-expanded-details">
            {hasReasoning && (
              <div className="detail-section">
                <h6>Why This Matters:</h6>
                <p>{finding.reasoning}</p>
              </div>
            )}

            {hasImplication && (
              <div className="detail-section">
                <h6>M&A Implications:</h6>
                <p>{finding.mna_implication}</p>
              </div>
            )}

            {hasMitigation && (
              <div className="detail-section">
                <h6>Mitigation Strategy:</h6>
                <p>{finding.mitigation}</p>
              </div>
            )}

            {finding.confidence && (
              <div className="detail-section">
                <h6>Confidence:</h6>
                <ConfidenceBadge confidence={finding.confidence} />
              </div>
            )}
          </div>
        </Collapse>

        {/* Source Facts Panel */}
        <Collapse in={showSources}>
          <div>
            <SourceFactsPanel factIds={finding.source_facts} />
          </div>
        </Collapse>
      </Card.Body>

      {/* Layer 4: Calculation Modal */}
      {showCalculation && (
        <CalculationModal
          finding={finding}
          onClose={() => setShowCalculation(false)}
        />
      )}
    </Card>
  );
};

export default FindingCard;
```

### 2. Calculation Transparency Modal

**Component:** `CalculationModal.jsx`

```jsx
import React, { useState } from 'react';
import { Modal, Tab, Tabs } from 'react-bootstrap';
import CostBreakdownView from './CostBreakdownView';
import ResourceBreakdownView from './ResourceBreakdownView';
import TreeView from './TreeView';

const CalculationModal = ({ finding, onClose }) => {
  const [activeTab, setActiveTab] = useState('cost');

  const costBuildup = finding.cost_buildup_json
    ? JSON.parse(finding.cost_buildup_json)
    : null;

  const resourceBuildup = finding.resource_buildup_json
    ? JSON.parse(finding.resource_buildup_json)
    : null;

  return (
    <Modal show={true} onHide={onClose} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Calculation Breakdown</Modal.Title>
      </Modal.Header>

      <Modal.Body>
        <Tabs activeKey={activeTab} onSelect={setActiveTab}>
          {costBuildup && (
            <Tab eventKey="cost" title="Cost Estimate">
              <CostBreakdownView costBuildup={costBuildup} />
            </Tab>
          )}

          {resourceBuildup && (
            <Tab eventKey="resource" title="Resource Estimate">
              <ResourceBreakdownView resourceBuildup={resourceBuildup} />
            </Tab>
          )}

          {costBuildup && resourceBuildup && (
            <Tab eventKey="combined" title="Resources → Cost">
              <div className="combined-view">
                <h6>Resource Requirements Drive Costs:</h6>
                <div className="link-diagram">
                  <div className="resource-summary">
                    <strong>Resources:</strong> {resourceBuildup.total_effort_pm} PM
                  </div>
                  <div className="arrow">→ × ${costBuildup.blended_rate_low}/PM →</div>
                  <div className="cost-summary">
                    <strong>Labor Cost:</strong> ${costBuildup.labor_cost_low?.toLocaleString()}
                  </div>
                </div>

                <ResourceBreakdownView resourceBuildup={resourceBuildup} compact={true} />
                <CostBreakdownView costBuildup={costBuildup} compact={true} />
              </div>
            </Tab>
          )}
        </Tabs>
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CalculationModal;
```

### 3. Cost Breakdown View

**Component:** `CostBreakdownView.jsx`

```jsx
import React from 'react';
import { ProgressBar, ListGroup } from 'react-bootstrap';

const CostBreakdownView = ({ costBuildup, compact = false }) => {
  const totalLow = costBuildup.cost_low;
  const totalHigh = costBuildup.cost_high;
  const laborLow = costBuildup.labor_cost_low || 0;
  const laborHigh = costBuildup.labor_cost_high || 0;
  const nonLaborLow = costBuildup.non_labor_cost_low || 0;
  const nonLaborHigh = costBuildup.non_labor_cost_high || 0;

  const laborPercent = totalLow > 0 ? (laborLow / totalLow) * 100 : 0;
  const nonLaborPercent = totalLow > 0 ? (nonLaborLow / totalLow) * 100 : 0;

  return (
    <div className="cost-breakdown-view">
      <div className="cost-summary">
        <h5>Total Cost: ${totalLow.toLocaleString()} - ${totalHigh.toLocaleString()}</h5>

        {/* Visual breakdown */}
        <div className="cost-distribution">
          <ProgressBar>
            <ProgressBar variant="primary" now={laborPercent} label={`Labor ${laborPercent.toFixed(0)}%`} />
            <ProgressBar variant="secondary" now={nonLaborPercent} label={`Non-Labor ${nonLaborPercent.toFixed(0)}%`} />
          </ProgressBar>
        </div>
      </div>

      {!compact && (
        <>
          {/* Labor Breakdown */}
          {laborLow > 0 && (
            <div className="cost-category">
              <h6>Labor Costs: ${laborLow.toLocaleString()} - ${laborHigh.toLocaleString()}</h6>

              {costBuildup.cost_components && costBuildup.cost_components.length > 0 && (
                <ListGroup variant="flush">
                  {costBuildup.cost_components
                    .filter(c => c.derived_from_role)
                    .map((component, idx) => (
                      <ListGroup.Item key={idx}>
                        <div className="component-row">
                          <div className="component-label">{component.label}</div>
                          <div className="component-value">
                            ${component.cost_low.toLocaleString()} - ${component.cost_high.toLocaleString()}
                          </div>
                        </div>
                        {component.quantity && component.unit && (
                          <div className="component-formula">
                            {component.quantity.toFixed(1)} {component.unit}
                          </div>
                        )}
                      </ListGroup.Item>
                    ))}
                </ListGroup>
              )}

              {costBuildup.blended_rate_low && (
                <div className="blended-rate-info">
                  <em>Blended Rate: ${costBuildup.blended_rate_low.toLocaleString()}/PM (±{((costBuildup.blended_rate_high / costBuildup.blended_rate_low - 1) * 100).toFixed(0)}%)</em>
                </div>
              )}
            </div>
          )}

          {/* Non-Labor Breakdown */}
          {nonLaborLow > 0 && (
            <div className="cost-category">
              <h6>Non-Labor Costs: ${nonLaborLow.toLocaleString()} - ${nonLaborHigh.toLocaleString()}</h6>

              <ListGroup variant="flush">
                {costBuildup.cost_components
                  .filter(c => !c.derived_from_role)
                  .map((component, idx) => (
                    <ListGroup.Item key={idx}>
                      <div className="component-row">
                        <div className="component-label">{component.label}</div>
                        <div className="component-value">
                          ${component.cost_low.toLocaleString()}
                          {component.cost_high !== component.cost_low && ` - $${component.cost_high.toLocaleString()}`}
                        </div>
                      </div>
                    </ListGroup.Item>
                  ))}
              </ListGroup>
            </div>
          )}

          {/* Assumptions */}
          {costBuildup.assumptions && costBuildup.assumptions.length > 0 && (
            <div className="assumptions-section">
              <h6>Assumptions:</h6>
              <ul>
                {costBuildup.assumptions.map((assumption, idx) => (
                  <li key={idx}>{assumption}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Metadata */}
          <div className="metadata-section">
            <div className="metadata-row">
              <span className="metadata-label">Estimation Method:</span>
              <span className="metadata-value">{costBuildup.estimation_method}</span>
            </div>
            {costBuildup.confidence && (
              <div className="metadata-row">
                <span className="metadata-label">Confidence:</span>
                <ConfidenceBadge confidence={costBuildup.confidence} />
              </div>
            )}
            {costBuildup.derived_from_resource_buildup && (
              <div className="metadata-row">
                <span className="badge bg-info">Auto-generated from resource estimate</span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default CostBreakdownView;
```

### 4. Resource Breakdown View

**Component:** `ResourceBreakdownView.jsx`

```jsx
import React from 'react';
import { Table, Badge, ListGroup } from 'react-bootstrap';

const ResourceBreakdownView = ({ resourceBuildup, compact = false }) => {
  const totalEffort = resourceBuildup.total_effort_pm;
  const peakHeadcount = resourceBuildup.peak_headcount;
  const duration = `${resourceBuildup.duration_months_low}-${resourceBuildup.duration_months_high} months`;

  return (
    <div className="resource-breakdown-view">
      <div className="resource-summary">
        <div className="summary-grid">
          <div className="summary-item">
            <div className="summary-label">Total Effort</div>
            <div className="summary-value">{totalEffort.toFixed(1)} PM</div>
          </div>
          <div className="summary-item">
            <div className="summary-label">Peak Team Size</div>
            <div className="summary-value">{peakHeadcount} FTEs</div>
          </div>
          <div className="summary-item">
            <div className="summary-label">Duration</div>
            <div className="summary-value">{duration}</div>
          </div>
        </div>
      </div>

      {!compact && (
        <>
          {/* Roles Breakdown */}
          {resourceBuildup.roles && resourceBuildup.roles.length > 0 && (
            <div className="roles-section">
              <h6>Role Breakdown:</h6>
              <Table striped bordered hover size="sm">
                <thead>
                  <tr>
                    <th>Role</th>
                    <th>FTE</th>
                    <th>Duration (mo)</th>
                    <th>Effort (PM)</th>
                    <th>Seniority</th>
                    <th>Sourcing</th>
                  </tr>
                </thead>
                <tbody>
                  {resourceBuildup.roles.map((role, idx) => (
                    <tr key={idx}>
                      <td>{role.role}</td>
                      <td>{role.fte.toFixed(1)}</td>
                      <td>{role.duration_months.toFixed(1)}</td>
                      <td>{role.effort_pm.toFixed(1)}</td>
                      <td>
                        <Badge bg="secondary">{role.seniority}</Badge>
                      </td>
                      <td>
                        <Badge bg="info">{role.sourcing_type || 'mixed'}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          )}

          {/* Skills Required */}
          {resourceBuildup.skills_required && resourceBuildup.skills_required.length > 0 && (
            <div className="skills-section">
              <h6>Skills Required:</h6>
              <div className="skills-badges">
                {resourceBuildup.skills_required.map((skill, idx) => (
                  <Badge key={idx} bg="light" text="dark" className="skill-badge">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Sourcing Mix */}
          {resourceBuildup.sourcing_mix && Object.keys(resourceBuildup.sourcing_mix).length > 0 && (
            <div className="sourcing-section">
              <h6>Sourcing Mix:</h6>
              <div className="sourcing-breakdown">
                {Object.entries(resourceBuildup.sourcing_mix).map(([type, fraction]) => (
                  <div key={type} className="sourcing-item">
                    <span className="sourcing-type">{type}:</span>
                    <span className="sourcing-value">{(fraction * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Assumptions */}
          {resourceBuildup.assumptions && resourceBuildup.assumptions.length > 0 && (
            <div className="assumptions-section">
              <h6>Assumptions:</h6>
              <ul>
                {resourceBuildup.assumptions.map((assumption, idx) => (
                  <li key={idx}>{assumption}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Metadata */}
          <div className="metadata-section">
            {resourceBuildup.confidence && (
              <div className="metadata-row">
                <span className="metadata-label">Confidence:</span>
                <ConfidenceBadge confidence={resourceBuildup.confidence} />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ResourceBreakdownView;
```

### 5. Source Facts Panel

**Component:** `SourceFactsPanel.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { ListGroup, Spinner, Alert } from 'react-bootstrap';
import { fetchFacts } from '../api/facts';

const SourceFactsPanel = ({ factIds }) => {
  const [facts, setFacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadFacts = async () => {
      try {
        setLoading(true);
        const fetchedFacts = await fetchFacts(factIds);
        setFacts(fetchedFacts);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (factIds && factIds.length > 0) {
      loadFacts();
    } else {
      setLoading(false);
    }
  }, [factIds]);

  if (loading) {
    return <Spinner animation="border" size="sm" />;
  }

  if (error) {
    return <Alert variant="danger">Error loading facts: {error}</Alert>;
  }

  if (facts.length === 0) {
    return <Alert variant="info">No source facts available</Alert>;
  }

  return (
    <div className="source-facts-panel">
      <h6>Source Evidence ({facts.length} facts):</h6>
      <ListGroup variant="flush">
        {facts.map((fact, idx) => (
          <ListGroup.Item key={idx} className="fact-item">
            <div className="fact-header">
              <Badge bg="secondary">{fact.id}</Badge>
              <span className="fact-category">{fact.category}</span>
            </div>
            <div className="fact-content">{fact.content}</div>
            {fact.source_document && (
              <div className="fact-source">
                <small>Source: {fact.source_document}</small>
              </div>
            )}
            {fact.confidence && (
              <ConfidenceBadge confidence={fact.confidence} size="sm" />
            )}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </div>
  );
};

export default SourceFactsPanel;
```

### 6. Confidence Badge Component

**Component:** `ConfidenceBadge.jsx`

```jsx
import React from 'react';
import { Badge, OverlayTrigger, Tooltip } from 'react-bootstrap';

const ConfidenceBadge = ({ confidence, size = 'md' }) => {
  const confidencePercent = (confidence * 100).toFixed(0);

  let variant, label, explanation;

  if (confidence >= 0.8) {
    variant = 'success';
    label = 'High';
    explanation = 'Based on verified, comprehensive data';
  } else if (confidence >= 0.6) {
    variant = 'warning';
    label = 'Medium';
    explanation = 'Based on incomplete or estimated data';
  } else {
    variant = 'danger';
    label = 'Low';
    explanation = 'Based on limited data or high uncertainty';
  }

  const tooltip = (
    <Tooltip>
      <strong>{label} Confidence ({confidencePercent}%)</strong>
      <div>{explanation}</div>
    </Tooltip>
  );

  return (
    <OverlayTrigger placement="top" overlay={tooltip}>
      <Badge bg={variant} className={`confidence-badge confidence-${size}`}>
        {label} ({confidencePercent}%)
      </Badge>
    </OverlayTrigger>
  );
};

export default ConfidenceBadge;
```

---

## CSS Styling

**File:** `web/static/css/explanatory-ui.css`

```css
/* ============= Finding Card ============= */

.finding-card {
  margin-bottom: 16px;
  border: 1px solid #d0d7de;
  border-radius: 8px;
  transition: box-shadow 0.2s;
}

.finding-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.finding-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.finding-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #24292f;
}

/* Inline Context */
.finding-inline-context {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: #f6f8fa;
  border-left: 3px solid #0969da;
  border-radius: 4px;
  margin-bottom: 12px;
}

.context-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.context-text {
  color: #24292f;
  font-size: 14px;
  line-height: 1.5;
}

/* Actions */
.finding-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #d0d7de;
}

.finding-actions .btn-link {
  padding: 4px 8px;
  font-size: 13px;
  text-decoration: none;
  color: #0969da;
}

.finding-actions .btn-link:hover {
  text-decoration: underline;
}

/* Expanded Details */
.finding-expanded-details {
  margin-top: 16px;
  padding: 16px;
  background: #f6f8fa;
  border-radius: 6px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h6 {
  font-size: 14px;
  font-weight: 600;
  color: #57606a;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-section p {
  margin: 0;
  color: #24292f;
  line-height: 1.6;
}

/* ============= Calculation Modal ============= */

.calculation-modal .modal-dialog {
  max-width: 900px;
}

.calculation-modal .modal-body {
  padding: 24px;
}

/* Cost Breakdown View */
.cost-breakdown-view {
  padding: 16px;
}

.cost-summary h5 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
}

.cost-distribution {
  margin: 16px 0;
}

.cost-category {
  margin-top: 24px;
}

.cost-category h6 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #d0d7de;
}

.component-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.component-label {
  font-weight: 500;
  color: #24292f;
}

.component-value {
  font-weight: 600;
  color: #0969da;
}

.component-formula {
  font-size: 12px;
  color: #57606a;
  margin-top: 4px;
}

.blended-rate-info {
  margin-top: 12px;
  padding: 8px 12px;
  background: #ddf4ff;
  border-left: 3px solid #0969da;
  border-radius: 4px;
  font-size: 13px;
}

.assumptions-section {
  margin-top: 24px;
  padding: 16px;
  background: #fff8c5;
  border-left: 3px solid #bf8700;
  border-radius: 4px;
}

.assumptions-section h6 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.assumptions-section ul {
  margin: 0;
  padding-left: 20px;
}

.assumptions-section li {
  margin-bottom: 4px;
  font-size: 13px;
}

.metadata-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #d0d7de;
}

.metadata-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}

.metadata-label {
  font-weight: 600;
  color: #57606a;
}

.metadata-value {
  color: #24292f;
}

/* Resource Breakdown View */
.resource-breakdown-view {
  padding: 16px;
}

.resource-summary {
  margin-bottom: 24px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.summary-item {
  padding: 16px;
  background: #f6f8fa;
  border-radius: 6px;
  text-align: center;
}

.summary-label {
  font-size: 12px;
  color: #57606a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.summary-value {
  font-size: 24px;
  font-weight: 600;
  color: #0969da;
}

.roles-section {
  margin-top: 24px;
}

.roles-section h6 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.roles-section table {
  font-size: 13px;
}

.skills-section {
  margin-top: 24px;
}

.skills-section h6 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.skills-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.skill-badge {
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
}

.sourcing-section {
  margin-top: 24px;
}

.sourcing-breakdown {
  display: flex;
  gap: 24px;
}

.sourcing-item {
  display: flex;
  gap: 8px;
}

.sourcing-type {
  font-weight: 600;
  text-transform: capitalize;
}

.sourcing-value {
  color: #0969da;
  font-weight: 600;
}

/* Source Facts Panel */
.source-facts-panel {
  margin-top: 16px;
  padding: 16px;
  background: #f6f8fa;
  border-radius: 6px;
}

.source-facts-panel h6 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.fact-item {
  padding: 12px;
  border-left: 3px solid #0969da;
}

.fact-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.fact-category {
  font-size: 12px;
  color: #57606a;
}

.fact-content {
  font-size: 14px;
  color: #24292f;
  margin-bottom: 4px;
}

.fact-source {
  font-size: 12px;
  color: #57606a;
}

/* Confidence Badge */
.confidence-badge {
  font-size: 12px;
  padding: 4px 8px;
  cursor: help;
}

.confidence-badge.confidence-sm {
  font-size: 11px;
  padding: 2px 6px;
}

.confidence-badge.confidence-lg {
  font-size: 14px;
  padding: 6px 12px;
}

/* Combined View */
.combined-view {
  padding: 16px;
}

.link-diagram {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 24px;
  background: #f6f8fa;
  border-radius: 8px;
  margin: 24px 0;
}

.resource-summary,
.cost-summary {
  padding: 16px;
  background: white;
  border: 2px solid #0969da;
  border-radius: 6px;
  font-size: 14px;
}

.arrow {
  font-size: 18px;
  font-weight: 600;
  color: #0969da;
}
```

---

## Backend API Updates

### Enhanced Finding Serialization

**File:** `web/api/findings.py`

```python
from flask import Blueprint, jsonify
from web.database import Finding

findings_api = Blueprint('findings_api', __name__)

@findings_api.route('/api/findings/<finding_id>', methods=['GET'])
def get_finding(finding_id):
    """
    Get finding with full explanatory context.

    Returns:
        {
            "id": "FND-12345",
            "title": "Legacy ERP System",
            "severity": "high",
            "reasoning": "Oracle E-Business Suite 11i is end-of-life...",
            "mna_implication": "Post-acquisition, this system will require...",
            "mitigation": "Phase 1: Assess upgrade vs replace...",
            "confidence": 0.85,
            "source_facts": ["F-APP-001", "F-APP-008", "F-INT-004"],
            "cost_buildup": {...},  # Full CostBuildUp object
            "resource_buildup": {...},  # Full ResourceBuildUp object
            "has_reasoning": true,
            "has_cost_buildup": true,
            "has_resource_buildup": true
        }
    """
    finding = Finding.query.get_or_404(finding_id)

    # Parse JSON fields
    cost_buildup = None
    if finding.cost_buildup_json:
        from specs.analysis_depth_enhancement.resource_cost_integration import CostBuildUp
        cost_buildup = CostBuildUp.from_dict(finding.cost_buildup_json)

    resource_buildup = None
    if finding.resource_buildup_json:
        from specs.analysis_depth_enhancement.resource_buildup_model import ResourceBuildUp
        resource_buildup = ResourceBuildUp.from_dict(finding.resource_buildup_json)

    return jsonify({
        "id": finding.id,
        "title": finding.title,
        "severity": finding.severity,
        "category": finding.category,
        "reasoning": finding.reasoning,
        "mna_implication": finding.mna_implication,
        "mitigation": finding.mitigation,
        "implication": finding.implication,
        "confidence": finding.confidence,
        "source_facts": finding.source_facts or [],
        "cost_buildup": cost_buildup.to_dict() if cost_buildup else None,
        "resource_buildup": resource_buildup.to_dict() if resource_buildup else None,
        # Convenience flags
        "has_reasoning": bool(finding.reasoning and finding.reasoning.strip()),
        "has_mna_implication": bool(finding.mna_implication and finding.mna_implication.strip()),
        "has_mitigation": bool(finding.mitigation and finding.mitigation.strip()),
        "has_cost_buildup": finding.cost_buildup_json is not None,
        "has_resource_buildup": finding.resource_buildup_json is not None,
        "has_source_facts": bool(finding.source_facts and len(finding.source_facts) > 0),
    })

@findings_api.route('/api/facts/batch', methods=['POST'])
def get_facts_batch():
    """
    Get multiple facts by IDs.

    Request:
        {"fact_ids": ["F-APP-001", "F-APP-008", ...]}

    Returns:
        {"facts": [{...}, {...}]}
    """
    from flask import request
    from web.database import Fact

    data = request.get_json()
    fact_ids = data.get('fact_ids', [])

    if not fact_ids:
        return jsonify({"facts": []})

    facts = Fact.query.filter(Fact.id.in_(fact_ids)).all()

    return jsonify({
        "facts": [
            {
                "id": fact.id,
                "content": fact.content,
                "category": fact.category,
                "source_document": fact.source_document,
                "confidence": fact.confidence,
                "metadata": fact.metadata,
            }
            for fact in facts
        ]
    })
```

---

## User Experience Improvements

### 1. Default Expanded State

**Problem:** Users may not know to click "Explain This"

**Solution:** Optionally auto-expand first finding or high-severity findings

```jsx
// In FindingsPage.jsx
const [expanded, setExpanded] = useState(() => {
  // Auto-expand high-severity findings
  return finding.severity === 'high';
});
```

### 2. Keyboard Shortcuts

**Enhancement:** Power users can expand/collapse with keyboard

```jsx
// Global keyboard handler
useEffect(() => {
  const handleKeyPress = (e) => {
    if (e.key === 'e' && e.ctrlKey) {
      // Ctrl+E: Expand all
      expandAllFindings();
    } else if (e.key === 'c' && e.ctrlKey) {
      // Ctrl+C: Collapse all
      collapseAllFindings();
    }
  };

  document.addEventListener('keydown', handleKeyPress);
  return () => document.removeEventListener('keydown', handleKeyPress);
}, []);
```

### 3. Inline Calculation Preview

**Enhancement:** Show cost/resource summary inline without opening modal

```jsx
<div className="inline-calculation-preview">
  {hasCostBuildup && (
    <span className="cost-preview">
      💰 ${costBuildup.cost_low / 1000}k - ${costBuildup.cost_high / 1000}k
    </span>
  )}
  {hasResourceBuildup && (
    <span className="resource-preview">
      👥 {resourceBuildup.total_effort_pm} PM ({resourceBuildup.peak_headcount} FTEs)
    </span>
  )}
</div>
```

### 4. Progressive Disclosure

**Pattern:** Show summary → details → full breakdown

```
Level 1: Title + inline context (always visible)
Level 2: Reasoning + implications (click "Explain This")
Level 3: Full calculation breakdown (click "View Calculation")
```

---

## Accessibility Considerations

### ARIA Labels

```jsx
<button
  aria-label="Explain why this finding matters"
  aria-expanded={expanded}
  onClick={() => setExpanded(!expanded)}
>
  {expanded ? 'Hide Details ▲' : 'Explain This ▼'}
</button>
```

### Keyboard Navigation

- All expand/collapse buttons focusable via Tab
- Enter/Space to toggle expansion
- Escape to close modals
- Arrow keys to navigate tree views

### Screen Reader Support

```jsx
<div role="region" aria-labelledby="finding-title-123">
  <h5 id="finding-title-123">{finding.title}</h5>
  {/* Content */}
</div>
```

---

## Performance Optimizations

### 1. Lazy Load Calculation Details

**Problem:** Loading all cost/resource buildups upfront is slow

**Solution:** Only load when modal opens

```jsx
const [calculation, setCalculation] = useState(null);

const handleOpenCalculation = async () => {
  setShowCalculation(true);
  if (!calculation) {
    const data = await fetchCalculationDetails(finding.id);
    setCalculation(data);
  }
};
```

### 2. Virtualized Lists

**Problem:** 50+ findings with expanded details slow down page

**Solution:** Use react-window for virtualized rendering

```jsx
import { FixedSizeList as List } from 'react-window';

<List
  height={600}
  itemCount={findings.length}
  itemSize={150}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <FindingCard finding={findings[index]} />
    </div>
  )}
</List>
```

### 3. Memoization

**Problem:** Re-rendering calculation views on every state change

**Solution:** Memoize components

```jsx
import { memo } from 'react';

const CostBreakdownView = memo(({ costBuildup }) => {
  // Component logic
}, (prevProps, nextProps) => {
  // Only re-render if cost buildup changed
  return prevProps.costBuildup.id === nextProps.costBuildup.id &&
         prevProps.costBuildup.version === nextProps.costBuildup.version;
});
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_explanatory_ui.py`

```python
import pytest
from web.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_finding_has_explanatory_flags(client):
    """Test that finding API returns has_* flags."""
    response = client.get('/api/findings/FND-TEST-001')
    data = response.get_json()

    assert 'has_reasoning' in data
    assert 'has_cost_buildup' in data
    assert 'has_resource_buildup' in data
    assert 'has_source_facts' in data

def test_batch_facts_endpoint(client):
    """Test batch fact fetching."""
    response = client.post('/api/facts/batch', json={
        "fact_ids": ["F-APP-001", "F-APP-002"]
    })
    data = response.get_json()

    assert 'facts' in data
    assert len(data['facts']) == 2
```

### Component Tests

**File:** `tests/ui/FindingCard.test.jsx`

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import FindingCard from '../components/FindingCard';

test('renders finding title and severity', () => {
  const finding = {
    id: 'FND-001',
    title: 'Test Finding',
    severity: 'high',
    reasoning: 'This is a test finding',
  };

  render(<FindingCard finding={finding} />);

  expect(screen.getByText('Test Finding')).toBeInTheDocument();
  expect(screen.getByText('HIGH')).toBeInTheDocument();
});

test('expands details when Explain This clicked', () => {
  const finding = {
    id: 'FND-001',
    title: 'Test Finding',
    severity: 'high',
    reasoning: 'This is a test finding with detailed reasoning',
  };

  render(<FindingCard finding={finding} />);

  // Initially collapsed
  expect(screen.queryByText(/detailed reasoning/i)).not.toBeVisible();

  // Click "Explain This"
  fireEvent.click(screen.getByText(/Explain This/i));

  // Now visible
  expect(screen.getByText(/detailed reasoning/i)).toBeVisible();
});

test('shows calculation modal when View Calculation clicked', () => {
  const finding = {
    id: 'FND-001',
    title: 'Test Finding',
    severity: 'high',
    cost_buildup_json: {
      cost_low: 100000,
      cost_high: 150000,
    },
  };

  render(<FindingCard finding={finding} />);

  // Click "View Calculation"
  fireEvent.click(screen.getByText(/View Calculation/i));

  // Modal should appear
  expect(screen.getByText(/Calculation Breakdown/i)).toBeInTheDocument();
});
```

---

## Implementation Checklist

### Phase 1: Core Components (Week 1)
- [ ] Implement FindingCard with expandable sections
- [ ] Add "Explain This", "View Calculation", "Source Facts" buttons
- [ ] Implement ConfidenceBadge component
- [ ] Write CSS styling
- [ ] Unit tests for components

### Phase 2: Calculation Views (Week 2)
- [ ] Implement CostBreakdownView
- [ ] Implement ResourceBreakdownView
- [ ] Implement CalculationModal
- [ ] Add combined resource → cost view
- [ ] Integration tests

### Phase 3: Source Facts (Week 2)
- [ ] Implement SourceFactsPanel
- [ ] Add batch facts API endpoint
- [ ] Link facts to source documents
- [ ] Add fact confidence displays

### Phase 4: Polish & UX (Week 3)
- [ ] Add keyboard shortcuts
- [ ] Implement lazy loading for calculations
- [ ] Add virtualized rendering for long lists
- [ ] Accessibility audit
- [ ] User testing & feedback

### Phase 5: Deployment (Week 3)
- [ ] Update API documentation
- [ ] Create user guide with screenshots
- [ ] Train deal teams
- [ ] Deploy to staging
- [ ] Production deployment

---

## Success Criteria

✅ **UI Enhancement successful when:**

1. **Visibility improved:** >80% of users see reasoning/implications (analytics)
2. **Engagement increased:** >40% click rate on "Explain This" buttons
3. **Calculation transparency:** >60% of findings with costs show breakdown
4. **User satisfaction:** >90% say "analysis provides sufficient context"
5. **Performance maintained:** Page load <2s with 50 findings
6. **Accessibility:** WCAG 2.1 AA compliance
7. **Feedback reduced:** "Too surface level" complaints drop >75%

---

## Document Status

**Status:** ✅ Ready for Implementation
**Dependencies:** Specs 01-04 (data models and hierarchy)
**Next Steps:** Proceed to Spec 06 (Fact Reasoning Expansion)

**Author:** Claude Sonnet 4.5
**Date:** February 10, 2026
**Version:** 1.0
