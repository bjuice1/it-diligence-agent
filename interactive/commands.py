"""
Command implementations for interactive CLI.

Each command is a function that takes (session, args) and returns output text.
"""

from typing import List, Optional, Callable, Dict
from pathlib import Path
from datetime import datetime

from .session import Session
from tools_v2.reasoning_tools import COST_RANGES


# Valid values for adjustments
VALID_SEVERITIES = ['critical', 'high', 'medium', 'low']
VALID_PHASES = ['Day_1', 'Day_100', 'Post_100']
VALID_PRIORITIES = ['critical', 'high', 'medium', 'low']
VALID_OWNERS = ['buyer', 'target', 'shared', 'vendor']
VALID_COST_ESTIMATES = COST_RANGES  # Already a list


def cmd_help(session: Session, args: List[str]) -> str:
    """Show help information."""
    if args:
        # Help for specific command
        cmd_name = args[0].lower()
        if cmd_name == 'shortcuts' or cmd_name == 'quick':
            return _quick_reference()
        if cmd_name in COMMAND_HELP:
            return COMMAND_HELP[cmd_name]
        else:
            return f"Unknown command: {cmd_name}\nType 'help' to see available commands."

    return """
============================================================
              IT DUE DILIGENCE - COMMAND REFERENCE
============================================================

GETTING AROUND
  d, dashboard       Visual summary of analysis
  s, status          Quick status check
  ?, help            This help screen
  q, exit            Leave interactive mode

VIEWING DATA                          SHORTCUTS
  list risks         All risks           lr
  list work-items    All work items      lw
  list facts         All facts           lf
  list gaps          Documentation gaps  lg
  explain <id>       Details for item    e <id>
  search "<text>"    Find items          find "<text>"

MAKING CHANGES
  adjust <id> <field> <value>     Change severity, phase, cost, owner
  note <id> "<text>"              Add a note to any finding
  delete <id>                     Remove a finding
  undo                            Revert last change

ADDING NEW ITEMS
  add risk "<title>" <severity> "<description>"
  add work-item "<title>" <phase> <cost>
  add fact <domain> "<description>"
  add gap <domain> "<description>"
  add context "<text>"            Deal-specific notes

SAVING WORK
  export             Save everything to files
  history            View all your changes

------------------------------------------------------------
  Type 'help <command>' for details on any command
  Type 'help shortcuts' for quick reference card
============================================================
"""


def _quick_reference() -> str:
    """Quick reference card for shortcuts."""
    return """
============================================================
                    QUICK REFERENCE CARD
============================================================

  SHORTCUTS                      EXAMPLES
  ---------                      --------
  d      Dashboard               d
  s      Status                  s
  lr     List risks              lr
  lw     List work items         lw
  lf     List facts              lf
  lg     List gaps               lg
  e      Explain                 e R-001
  a      Adjust                  a R-001 severity high
  n      Note                    n R-001 "verified"
  u      Undo                    u
  x      Export                  x
  q      Quit                    q

  COMMON ADJUSTMENTS
  ------------------
  adjust R-001 severity critical/high/medium/low
  adjust WI-001 phase Day_1/Day_100/Post_100
  adjust WI-001 cost under_25k/25k_to_100k/100k_to_500k
  adjust WI-001 owner buyer/target/shared/vendor

  DOMAINS FOR ADD COMMANDS
  ------------------------
  infrastructure, network, cybersecurity,
  applications, identity_access, organization

============================================================
"""


COMMAND_HELP = {
    'status': """
status - Show session summary

Usage: status

Shows:
  - Count of facts, gaps, risks, work items
  - Risk breakdown by severity
  - Cost summary by phase
  - Unsaved changes count
""",

    'list': """
list - List items

Usage:
  list facts          List all extracted facts
  list risks          List all identified risks
  list work-items     List all work items
  list gaps           List all gaps
  list all            List everything

Options:
  list risks --severity high    Filter by severity
  list work-items --phase Day_1 Filter by phase
  list facts --domain network   Filter by domain
""",

    'explain': """
explain - Show details for an item

Usage: explain <id>

Examples:
  explain R-001       Show risk R-001 with reasoning
  explain WI-003      Show work item WI-003
  explain F-INFRA-005 Show fact with evidence

Shows:
  - All fields for the item
  - Reasoning chain
  - Evidence citations
  - Related items
""",

    'adjust': """
adjust - Modify a field on an item

Usage: adjust <id> <field> <value>

For Risks (R-XXX):
  adjust R-001 severity critical
  adjust R-001 severity high/medium/low

For Work Items (WI-XXX):
  adjust WI-001 phase Day_1/Day_100/Post_100
  adjust WI-001 priority critical/high/medium/low
  adjust WI-001 owner buyer/target/shared/vendor
  adjust WI-001 cost under_25k/25k_to_100k/100k_to_500k/500k_to_1m/over_1m

All changes are tracked and can be undone with 'undo'.
""",

    'undo': """
undo - Undo last modification

Usage: undo

Reverts the most recent adjustment. Can be called multiple times
to undo multiple changes.
""",

    'export': """
export - Save outputs to files

Usage:
  export                    Save all outputs with timestamp
  export --format json      Export as JSON (default)
  export --format markdown  Export as Markdown

Output files are saved to the output/ directory.
""",

    'add': """
add - Add items manually

Usage:
  add context "<text>"                           Add deal context note
  add fact <domain> "<description>"              Add manual fact
  add risk "<title>" <severity> "<description>"  Add manual risk
  add work-item "<title>" <phase> <cost>         Add manual work item
  add gap <domain> "<description>"               Add manual gap

Examples:
  add context "Healthcare deal - HIPAA applies"
  add fact infrastructure "Primary DC is in Chicago"
  add risk "No SIEM deployed" high "No centralized security monitoring"
  add work-item "Deploy SIEM solution" Day_100 100k_to_500k
  add gap cybersecurity "Missing penetration test results"

Valid domains: infrastructure, network, cybersecurity, applications, identity_access, organization
Valid severities: critical, high, medium, low
Valid phases: Day_1, Day_100, Post_100
Valid costs: under_25k, 25k_to_100k, 100k_to_500k, 500k_to_1m, over_1m
""",

    'delete': """
delete - Remove a finding

Usage: delete <id>

Examples:
  delete R-003       Delete risk R-003
  delete WI-005      Delete work item WI-005
  delete F-INFRA-007 Delete fact F-INFRA-007

Note: Deleted items cannot be recovered (use 'export' first to save state).
""",

    'note': """
note - Add a note to a finding

Usage: note <id> "<text>"

Examples:
  note R-001 "Discussed with CTO - confirmed critical"
  note WI-003 "Buyer to fund this work item"

Notes are tracked as modifications and included in exports.
""",

    'search': """
search - Search across all items

Usage: search "<query>"

Examples:
  search "VMware"
  search "security"
  search "Day_1"

Searches titles, descriptions, and details of all items.
""",

    'clear': """
clear - Clear items

Usage:
  clear context     Remove all deal context
""",

    'history': """
history - Show modification history

Usage: history

Shows all modifications made during this session, including:
  - Adjustments to severities, phases, costs
  - Notes added to findings
  - Timestamp of each change

The history also shows which modifications have been saved.
"""
}


def cmd_status(session: Session, args: List[str]) -> str:
    """Show session status summary."""
    summary = session.get_summary()

    output = []
    output.append("\n" + "=" * 50)
    output.append("SESSION STATUS")
    output.append("=" * 50)

    output.append(f"\nFacts:    {summary['facts']}")
    output.append(f"Gaps:     {summary['gaps']}")
    output.append(f"Risks:    {summary['risks']}")
    output.append(f"Work Items: {summary['work_items']}")
    output.append(f"Strategic:  {summary['strategic_considerations']}")
    output.append(f"Recommendations: {summary['recommendations']}")

    if summary['domains_with_facts']:
        output.append(f"\nDomains: {', '.join(summary['domains_with_facts'])}")

    output.append(f"\nRisks by Severity:")
    risk_sum = summary['risk_summary']
    output.append(f"  Critical: {risk_sum['critical']}")
    output.append(f"  High:     {risk_sum['high']}")
    output.append(f"  Medium:   {risk_sum['medium']}")
    output.append(f"  Low:      {risk_sum['low']}")

    cost_sum = summary['cost_summary']
    output.append(f"\nCost by Phase:")
    for phase in ['Day_1', 'Day_100', 'Post_100']:
        if cost_sum[phase]['count'] > 0:
            low = cost_sum[phase]['low']
            high = cost_sum[phase]['high']
            output.append(f"  {phase}: ${low:,} - ${high:,} ({cost_sum[phase]['count']} items)")

    output.append(f"\nModifications: {summary['modifications']}")
    if summary['unsaved_changes'] > 0:
        output.append(f"  ⚠ {summary['unsaved_changes']} unsaved changes")

    if summary['has_deal_context']:
        output.append(f"\nDeal context: Set")

    return "\n".join(output)


def cmd_list(session: Session, args: List[str]) -> str:
    """List items."""
    if not args:
        return "Usage: list <facts|risks|work-items|gaps|all> [--filter value]"

    item_type = args[0].lower()

    # Parse filters
    filters = {}
    i = 1
    while i < len(args):
        if args[i].startswith('--') and i + 1 < len(args):
            filters[args[i][2:]] = args[i + 1]
            i += 2
        else:
            i += 1

    if item_type == 'facts':
        return _list_facts(session, filters)
    elif item_type == 'risks':
        return _list_risks(session, filters)
    elif item_type in ['work-items', 'workitems', 'wi']:
        return _list_work_items(session, filters)
    elif item_type == 'gaps':
        return _list_gaps(session, filters)
    elif item_type == 'all':
        parts = [
            _list_facts(session, filters),
            _list_risks(session, filters),
            _list_work_items(session, filters),
            _list_gaps(session, filters)
        ]
        return "\n".join(parts)
    else:
        return f"Unknown item type: {item_type}\nValid types: facts, risks, work-items, gaps, all"


def _list_facts(session: Session, filters: Dict) -> str:
    """List facts with optional filters."""
    facts = session.fact_store.facts

    # Apply filters
    if 'domain' in filters:
        facts = [f for f in facts if f.domain == filters['domain']]

    if not facts:
        return "\nFacts: (none)"

    output = [f"\n{'='*50}", "FACTS", f"{'='*50}"]

    # Group by domain
    by_domain = {}
    for fact in facts:
        if fact.domain not in by_domain:
            by_domain[fact.domain] = []
        by_domain[fact.domain].append(fact)

    for domain in sorted(by_domain.keys()):
        output.append(f"\n[{domain.upper()}]")
        for fact in by_domain[domain]:
            output.append(f"  {fact.fact_id}: {fact.item}")
            if fact.details:
                details_str = ", ".join(f"{k}={v}" for k, v in list(fact.details.items())[:3])
                output.append(f"    {details_str}")

    return "\n".join(output)


def _list_risks(session: Session, filters: Dict) -> str:
    """List risks with optional filters."""
    risks = session.reasoning_store.risks

    # Apply filters
    if 'severity' in filters:
        risks = [r for r in risks if r.severity == filters['severity']]
    if 'domain' in filters:
        risks = [r for r in risks if r.domain == filters['domain']]

    if not risks:
        return "\nRisks: (none)"

    output = [f"\n{'='*50}", "RISKS", f"{'='*50}"]

    # Sort by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    risks = sorted(risks, key=lambda r: severity_order.get(r.severity, 99))

    for risk in risks:
        severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(risk.severity, '⚪')
        output.append(f"\n  {risk.finding_id}: {risk.title}")
        output.append(f"    Severity: {severity_icon} {risk.severity.upper()}")
        output.append(f"    Domain: {risk.domain}")
        if risk.based_on_facts:
            output.append(f"    Evidence: {', '.join(risk.based_on_facts)}")

    return "\n".join(output)


def _list_work_items(session: Session, filters: Dict) -> str:
    """List work items with optional filters."""
    work_items = session.reasoning_store.work_items

    # Apply filters
    if 'phase' in filters:
        work_items = [w for w in work_items if w.phase == filters['phase']]
    if 'domain' in filters:
        work_items = [w for w in work_items if w.domain == filters['domain']]
    if 'owner' in filters:
        work_items = [w for w in work_items if w.owner_type == filters['owner']]

    if not work_items:
        return "\nWork Items: (none)"

    output = [f"\n{'='*50}", "WORK ITEMS", f"{'='*50}"]

    # Group by phase
    by_phase = {'Day_1': [], 'Day_100': [], 'Post_100': []}
    for wi in work_items:
        if wi.phase in by_phase:
            by_phase[wi.phase].append(wi)

    for phase in ['Day_1', 'Day_100', 'Post_100']:
        if by_phase[phase]:
            output.append(f"\n[{phase}]")
            for wi in by_phase[phase]:
                output.append(f"  {wi.finding_id}: {wi.title}")
                output.append(f"    Cost: {wi.cost_estimate} | Owner: {wi.owner_type} | Priority: {wi.priority}")

    return "\n".join(output)


def _list_gaps(session: Session, filters: Dict) -> str:
    """List gaps with optional filters."""
    gaps = session.fact_store.gaps

    # Apply filters
    if 'domain' in filters:
        gaps = [g for g in gaps if g.domain == filters['domain']]

    if not gaps:
        return "\nGaps: (none)"

    output = [f"\n{'='*50}", "GAPS", f"{'='*50}"]

    # Group by domain
    by_domain = {}
    for gap in gaps:
        if gap.domain not in by_domain:
            by_domain[gap.domain] = []
        by_domain[gap.domain].append(gap)

    for domain in sorted(by_domain.keys()):
        output.append(f"\n[{domain.upper()}]")
        for gap in by_domain[domain]:
            importance_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(gap.importance, '⚪')
            output.append(f"  {gap.gap_id}: {gap.description}")
            output.append(f"    Importance: {importance_icon} {gap.importance}")

    return "\n".join(output)


def cmd_explain(session: Session, args: List[str]) -> str:
    """Explain an item in detail with connected items for navigation."""
    if not args:
        return "Usage: explain <id>\nExample: explain R-001"

    item_id = args[0]  # Keep original case for hash-based IDs
    result = session.get_item_by_id(item_id)

    if not result:
        return f"Item not found: {item_id}\n\nTip: Use 'lr' to list risks, 'lw' for work items, 'lf' for facts"

    item_type, item = result

    output = []
    output.append("")
    output.append("=" * 60)
    output.append(f"  {item_id}")
    output.append("=" * 60)

    if item_type == 'risk':
        output.append("")
        output.append(f"  RISK: {item.title}")
        output.append(f"  " + "-" * 50)
        output.append("")
        output.append(f"  Severity:    {item.severity.upper()}")
        output.append(f"  Domain:      {item.domain}")
        output.append(f"  Category:    {item.category}")
        output.append(f"  Integration: {'Yes - depends on integration approach' if item.integration_dependent else 'No - exists regardless'}")
        output.append(f"  Confidence:  {item.confidence}")
        output.append("")
        output.append("  DESCRIPTION")
        output.append("  " + "-" * 50)
        # Wrap description
        desc_lines = _wrap_text(item.description, 54)
        for line in desc_lines:
            output.append(f"  {line}")

        output.append("")
        output.append("  MITIGATION")
        output.append("  " + "-" * 50)
        mit_lines = _wrap_text(item.mitigation, 54)
        for line in mit_lines:
            output.append(f"  {line}")

        output.append("")
        output.append("  REASONING")
        output.append("  " + "-" * 50)
        reason_lines = _wrap_text(item.reasoning, 54)
        for line in reason_lines:
            output.append(f"  {line}")

        # Connected items - THE KEY NAVIGATION
        if item.based_on_facts:
            output.append("")
            output.append("  " + "=" * 50)
            output.append("  EVIDENCE - Supporting Facts")
            output.append("  " + "=" * 50)
            output.append("")
            for fact_id in item.based_on_facts:
                fact = session.get_fact(fact_id)
                if fact:
                    output.append(f"  >> {fact_id}")
                    output.append(f"     {fact.item}")
                    if fact.evidence and fact.evidence.get('exact_quote'):
                        quote = fact.evidence['exact_quote'][:80]
                        output.append(f"     \"{quote}...\"")
                    output.append("")

            output.append("  To view a fact: explain " + item.based_on_facts[0])

        # Find related work items
        related_wi = _find_related_work_items(session, item_id)
        if related_wi:
            output.append("")
            output.append("  " + "=" * 50)
            output.append("  RELATED - Work Items for this Risk")
            output.append("  " + "=" * 50)
            output.append("")
            for wi in related_wi:
                output.append(f"  >> {wi.finding_id}: {wi.title}")
                output.append(f"     Phase: {wi.phase} | Cost: {wi.cost_estimate}")
            output.append("")
            output.append(f"  To view work item: explain {related_wi[0].finding_id}")

        # Quick actions
        output.append("")
        output.append("  " + "-" * 50)
        output.append("  QUICK ACTIONS")
        output.append("  " + "-" * 50)
        output.append(f"  adjust {item_id} severity <critical|high|medium|low>")
        output.append(f"  note {item_id} \"your note here\"")
        output.append(f"  delete {item_id}")

    elif item_type == 'work_item':
        output.append("")
        output.append(f"  WORK ITEM: {item.title}")
        output.append(f"  " + "-" * 50)
        output.append("")
        output.append(f"  Phase:       {item.phase}")
        output.append(f"  Priority:    {item.priority}")
        output.append(f"  Owner:       {item.owner_type}")
        output.append(f"  Cost:        {item.cost_estimate}")
        output.append(f"  Domain:      {item.domain}")
        output.append(f"  Confidence:  {item.confidence}")

        # Cost breakdown
        cost_range = item.get_cost_range()
        output.append("")
        output.append(f"  Cost Range:  ${cost_range['low']:,} - ${cost_range['high']:,}")

        output.append("")
        output.append("  DESCRIPTION")
        output.append("  " + "-" * 50)
        desc_lines = _wrap_text(item.description, 54)
        for line in desc_lines:
            output.append(f"  {line}")

        output.append("")
        output.append("  REASONING")
        output.append("  " + "-" * 50)
        reason_lines = _wrap_text(item.reasoning, 54)
        for line in reason_lines:
            output.append(f"  {line}")

        # Connected items
        if item.triggered_by or item.triggered_by_risks:
            output.append("")
            output.append("  " + "=" * 50)
            output.append("  TRIGGERED BY")
            output.append("  " + "=" * 50)
            output.append("")

            if item.triggered_by_risks:
                output.append("  Risks:")
                for risk_id in item.triggered_by_risks:
                    risk = session.get_risk(risk_id)
                    if risk:
                        output.append(f"  >> {risk_id}: {risk.title}")
                output.append("")

            if item.triggered_by:
                output.append("  Facts:")
                for fact_id in item.triggered_by:
                    fact = session.get_fact(fact_id)
                    if fact:
                        output.append(f"  >> {fact_id}: {fact.item}")
                output.append("")

        # Quick actions
        output.append("")
        output.append("  " + "-" * 50)
        output.append("  QUICK ACTIONS")
        output.append("  " + "-" * 50)
        output.append(f"  adjust {item_id} phase <Day_1|Day_100|Post_100>")
        output.append(f"  adjust {item_id} cost <under_25k|25k_to_100k|100k_to_500k|...>")
        output.append(f"  adjust {item_id} owner <buyer|target|shared|vendor>")
        output.append(f"  note {item_id} \"your note here\"")

    elif item_type == 'fact':
        output.append("")
        output.append(f"  FACT: {item.item}")
        output.append(f"  " + "-" * 50)
        output.append("")
        output.append(f"  Domain:      {item.domain}")
        output.append(f"  Category:    {item.category}")
        output.append(f"  Status:      {item.status}")

        if item.details:
            output.append("")
            output.append("  DETAILS")
            output.append("  " + "-" * 50)
            for k, v in item.details.items():
                output.append(f"  {k}: {v}")

        if item.evidence:
            output.append("")
            output.append("  EVIDENCE")
            output.append("  " + "-" * 50)
            if item.evidence.get('exact_quote'):
                output.append(f"  Quote:")
                quote_lines = _wrap_text(item.evidence['exact_quote'], 52)
                for line in quote_lines:
                    output.append(f"    \"{line}\"")
            if item.evidence.get('source_section'):
                output.append(f"  Source: {item.evidence['source_section']}")

        # Find items that cite this fact
        citing_risks = _find_citing_risks(session, item_id)
        citing_wi = _find_citing_work_items(session, item_id)

        if citing_risks or citing_wi:
            output.append("")
            output.append("  " + "=" * 50)
            output.append("  USED BY - Items citing this fact")
            output.append("  " + "=" * 50)
            output.append("")

            if citing_risks:
                output.append("  Risks:")
                for risk in citing_risks:
                    output.append(f"  >> {risk.finding_id}: {risk.title} ({risk.severity})")
                output.append("")

            if citing_wi:
                output.append("  Work Items:")
                for wi in citing_wi:
                    output.append(f"  >> {wi.finding_id}: {wi.title}")
                output.append("")

    elif item_type == 'gap':
        output.append("")
        output.append(f"  GAP: {item.description}")
        output.append(f"  " + "-" * 50)
        output.append("")
        output.append(f"  Domain:      {item.domain}")
        output.append(f"  Category:    {item.category}")
        output.append(f"  Importance:  {item.importance}")

        output.append("")
        output.append("  This is missing information that should be requested.")
        output.append("  Consider adding to VDR (Vendor Due Diligence Request).")

    elif item_type == 'strategic_consideration':
        output.append("")
        output.append(f"  STRATEGIC: {item.title}")
        output.append(f"  " + "-" * 50)
        output.append("")
        output.append(f"  Domain:      {item.domain}")
        output.append(f"  Lens:        {item.lens}")

        output.append("")
        output.append("  DESCRIPTION")
        output.append("  " + "-" * 50)
        desc_lines = _wrap_text(item.description, 54)
        for line in desc_lines:
            output.append(f"  {line}")

        output.append("")
        output.append("  IMPLICATION")
        output.append("  " + "-" * 50)
        impl_lines = _wrap_text(item.implication, 54)
        for line in impl_lines:
            output.append(f"  {line}")

    elif item_type == 'recommendation':
        output.append("")
        output.append(f"  RECOMMENDATION: {item.title}")
        output.append(f"  " + "-" * 50)
        output.append("")
        output.append(f"  Domain:      {item.domain}")
        output.append(f"  Action Type: {item.action_type}")
        output.append(f"  Urgency:     {item.urgency}")

        output.append("")
        output.append("  DESCRIPTION")
        output.append("  " + "-" * 50)
        desc_lines = _wrap_text(item.description, 54)
        for line in desc_lines:
            output.append(f"  {line}")

        output.append("")
        output.append("  RATIONALE")
        output.append("  " + "-" * 50)
        rat_lines = _wrap_text(item.rationale, 54)
        for line in rat_lines:
            output.append(f"  {line}")

    output.append("")
    return "\n".join(output)


def _wrap_text(text: str, width: int) -> List[str]:
    """Wrap text to specified width."""
    if not text:
        return ["(none)"]

    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(" ".join(current_line))

    return lines if lines else ["(none)"]


def _find_related_work_items(session: Session, risk_id: str) -> List:
    """Find work items triggered by this risk."""
    related = []
    for wi in session.reasoning_store.work_items:
        if hasattr(wi, 'triggered_by_risks') and wi.triggered_by_risks:
            if risk_id in wi.triggered_by_risks:
                related.append(wi)
    return related


def _find_citing_risks(session: Session, fact_id: str) -> List:
    """Find risks that cite this fact."""
    citing = []
    for risk in session.reasoning_store.risks:
        if hasattr(risk, 'based_on_facts') and risk.based_on_facts:
            if fact_id in risk.based_on_facts:
                citing.append(risk)
    return citing


def _find_citing_work_items(session: Session, fact_id: str) -> List:
    """Find work items that cite this fact."""
    citing = []
    for wi in session.reasoning_store.work_items:
        if hasattr(wi, 'triggered_by') and wi.triggered_by:
            if fact_id in wi.triggered_by:
                citing.append(wi)
        if hasattr(wi, 'based_on_facts') and wi.based_on_facts:
            if fact_id in wi.based_on_facts:
                citing.append(wi)
    return list(set(citing))  # Remove duplicates


def cmd_adjust(session: Session, args: List[str]) -> str:
    """Adjust a field on an item."""
    if len(args) < 3:
        return "Usage: adjust <id> <field> <value>\nExample: adjust R-001 severity critical"

    item_id = args[0]  # Keep original case for hash-based IDs
    field = args[1].lower()
    value = args[2]

    # Get item type
    result = session.get_item_by_id(item_id)
    if not result:
        return f"Item not found: {item_id}"

    item_type, item = result

    # Validate based on item type and field
    if item_type == 'risk':
        if field == 'severity':
            if value not in VALID_SEVERITIES:
                return f"Invalid severity. Valid values: {', '.join(VALID_SEVERITIES)}"
            old_value = item.severity
            if session.adjust_risk(item_id, 'severity', value):
                return f"✓ {item_id} severity: {old_value} → {value}"
        elif field == 'category':
            old_value = item.category
            if session.adjust_risk(item_id, 'category', value):
                return f"✓ {item_id} category: {old_value} → {value}"
        else:
            return f"Cannot adjust '{field}' on risks. Valid fields: severity, category"

    elif item_type == 'work_item':
        if field == 'phase':
            if value not in VALID_PHASES:
                return f"Invalid phase. Valid values: {', '.join(VALID_PHASES)}"
            old_value = item.phase
            if session.adjust_work_item(item_id, 'phase', value):
                return f"✓ {item_id} phase: {old_value} → {value}"
        elif field == 'priority':
            if value not in VALID_PRIORITIES:
                return f"Invalid priority. Valid values: {', '.join(VALID_PRIORITIES)}"
            old_value = item.priority
            if session.adjust_work_item(item_id, 'priority', value):
                return f"✓ {item_id} priority: {old_value} → {value}"
        elif field == 'owner':
            if value not in VALID_OWNERS:
                return f"Invalid owner. Valid values: {', '.join(VALID_OWNERS)}"
            old_value = item.owner_type
            if session.adjust_work_item(item_id, 'owner_type', value):
                return f"✓ {item_id} owner: {old_value} → {value}"
        elif field == 'cost':
            if value not in VALID_COST_ESTIMATES:
                return f"Invalid cost. Valid values: {', '.join(VALID_COST_ESTIMATES)}"
            old_value = item.cost_estimate
            if session.adjust_work_item(item_id, 'cost_estimate', value):
                return f"✓ {item_id} cost: {old_value} → {value}"
        else:
            return f"Cannot adjust '{field}' on work items. Valid fields: phase, priority, owner, cost"

    else:
        return f"Cannot adjust items of type '{item_type}'. Only risks and work items can be adjusted."

    return f"Failed to adjust {item_id}"


def cmd_undo(session: Session, args: List[str]) -> str:
    """Undo last modification."""
    mod = session.undo_last()

    if not mod:
        return "Nothing to undo."

    return f"✓ Undone: {mod.item_id} {mod.field}: {mod.new_value} → {mod.old_value}"


VALID_DOMAINS = ['infrastructure', 'network', 'cybersecurity', 'applications', 'identity_access', 'organization']


def cmd_add(session: Session, args: List[str]) -> str:
    """Add items (context, facts, risks, work items, gaps)."""
    if not args:
        return "Usage: add <context|fact|risk|work-item|gap> ...\nType 'help add' for details."

    sub_cmd = args[0].lower()

    if sub_cmd == 'context':
        if len(args) < 2:
            return "Usage: add context \"<text>\""
        context_text = " ".join(args[1:]).strip('"\'')
        session.add_deal_context(context_text)
        return f"✓ Added deal context: \"{context_text}\""

    elif sub_cmd == 'fact':
        # add fact <domain> "<description>"
        if len(args) < 3:
            return "Usage: add fact <domain> \"<description>\"\nExample: add fact infrastructure \"Primary DC in Chicago\""
        domain = args[1].lower()
        if domain not in VALID_DOMAINS:
            return f"Invalid domain. Valid domains: {', '.join(VALID_DOMAINS)}"
        description = " ".join(args[2:]).strip('"\'')

        fact_id = session.fact_store.add_fact(
            domain=domain,
            category="manual_entry",
            item=description,
            details={"source": "manual", "added_via": "interactive_cli"},
            status="documented",
            evidence={"exact_quote": f"[Manual entry: {description}]", "source_section": "Interactive CLI"}
        )
        return f"✓ Added fact {fact_id}: {description}"

    elif sub_cmd == 'risk':
        # add risk "<title>" <severity> "<description>"
        if len(args) < 4:
            return "Usage: add risk \"<title>\" <severity> \"<description>\"\nExample: add risk \"No SIEM\" high \"No centralized monitoring\""
        title = args[1].strip('"\'')
        severity = args[2].lower()
        if severity not in VALID_SEVERITIES:
            return f"Invalid severity. Valid: {', '.join(VALID_SEVERITIES)}"
        description = " ".join(args[3:]).strip('"\'')

        risk_id = session.reasoning_store.add_risk(
            domain="manual",
            title=title,
            description=description,
            category="manual_entry",
            severity=severity,
            integration_dependent=False,
            mitigation="[To be determined]",
            based_on_facts=[],
            confidence="medium",
            reasoning="[Manual entry via interactive CLI]"
        )
        return f"✓ Added risk {risk_id}: {title} ({severity})"

    elif sub_cmd in ['work-item', 'workitem', 'wi']:
        # add work-item "<title>" <phase> <cost>
        if len(args) < 4:
            return "Usage: add work-item \"<title>\" <phase> <cost>\nExample: add work-item \"Deploy SIEM\" Day_100 100k_to_500k"
        title = args[1].strip('"\'')
        phase = args[2]
        if phase not in VALID_PHASES:
            return f"Invalid phase. Valid: {', '.join(VALID_PHASES)}"
        cost = args[3]
        if cost not in VALID_COST_ESTIMATES:
            return f"Invalid cost. Valid: {', '.join(VALID_COST_ESTIMATES)}"

        wi_id = session.reasoning_store.add_work_item(
            domain="manual",
            title=title,
            description=f"[Manual entry: {title}]",
            phase=phase,
            priority="medium",
            owner_type="target",
            triggered_by=[],
            based_on_facts=[],
            confidence="medium",
            reasoning="[Manual entry via interactive CLI]",
            cost_estimate=cost
        )
        return f"✓ Added work item {wi_id}: {title} ({phase}, {cost})"

    elif sub_cmd == 'gap':
        # add gap <domain> "<description>"
        if len(args) < 3:
            return "Usage: add gap <domain> \"<description>\"\nExample: add gap cybersecurity \"Missing pen test results\""
        domain = args[1].lower()
        if domain not in VALID_DOMAINS:
            return f"Invalid domain. Valid domains: {', '.join(VALID_DOMAINS)}"
        description = " ".join(args[2:]).strip('"\'')

        gap_id = session.fact_store.add_gap(
            domain=domain,
            category="manual_entry",
            description=description,
            importance="medium"
        )
        return f"✓ Added gap {gap_id}: {description}"

    return f"Unknown add command: {sub_cmd}\nValid: context, fact, risk, work-item, gap"


def cmd_clear(session: Session, args: List[str]) -> str:
    """Clear items."""
    if not args:
        return "Usage: clear context"

    sub_cmd = args[0].lower()

    if sub_cmd == 'context':
        session.clear_deal_context()
        return "✓ Deal context cleared"

    return f"Unknown clear command: {sub_cmd}\nValid: clear context"


def cmd_show(session: Session, args: List[str]) -> str:
    """Show specific information."""
    if not args:
        return "Usage: show context"

    sub_cmd = args[0].lower()

    if sub_cmd == 'context':
        if not session.deal_context:
            return "No deal context set."

        output = ["\nDeal Context:"]
        for note in session.deal_context.get('notes', []):
            output.append(f"  • {note['text']}")
            output.append(f"    (added: {note['added_at']})")
        return "\n".join(output)

    return f"Unknown show command: {sub_cmd}\nValid: show context"


def cmd_export(session: Session, args: List[str]) -> str:
    """Export session to files."""
    # Parse format option
    format_type = 'json'
    i = 0
    while i < len(args):
        if args[i] == '--format' and i + 1 < len(args):
            format_type = args[i + 1].lower()
            i += 2
        else:
            i += 1

    # Get output directory
    from config_v2 import OUTPUT_DIR
    output_dir = OUTPUT_DIR

    # Save files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_files = session.save_to_files(output_dir, timestamp)

    output = ["\n✓ Exported files:"]
    for file_type, file_path in saved_files.items():
        output.append(f"  {file_type}: {file_path}")

    return "\n".join(output)


def cmd_delete(session: Session, args: List[str]) -> str:
    """Delete a finding."""
    if not args:
        return "Usage: delete <id>\nExample: delete R-001"

    item_id = args[0]  # Keep original case for hash-based IDs
    result = session.get_item_by_id(item_id)

    if not result:
        return f"Item not found: {item_id}"

    item_type, item = result

    # Delete based on type
    if item_type == 'risk':
        session.reasoning_store.risks = [r for r in session.reasoning_store.risks if r.finding_id != item_id]
        return f"✓ Deleted risk {item_id}: {item.title}"

    elif item_type == 'work_item':
        session.reasoning_store.work_items = [w for w in session.reasoning_store.work_items if w.finding_id != item_id]
        return f"✓ Deleted work item {item_id}: {item.title}"

    elif item_type == 'strategic_consideration':
        session.reasoning_store.strategic_considerations = [s for s in session.reasoning_store.strategic_considerations if s.finding_id != item_id]
        return f"✓ Deleted strategic consideration {item_id}: {item.title}"

    elif item_type == 'recommendation':
        session.reasoning_store.recommendations = [r for r in session.reasoning_store.recommendations if r.finding_id != item_id]
        return f"✓ Deleted recommendation {item_id}: {item.title}"

    elif item_type == 'fact':
        session.fact_store.facts = [f for f in session.fact_store.facts if f.fact_id != item_id]
        return f"✓ Deleted fact {item_id}: {item.item}"

    elif item_type == 'gap':
        session.fact_store.gaps = [g for g in session.fact_store.gaps if g.gap_id != item_id]
        return f"✓ Deleted gap {item_id}: {item.description}"

    return f"Cannot delete items of type '{item_type}'"


def cmd_note(session: Session, args: List[str]) -> str:
    """Add a note to a finding."""
    if len(args) < 2:
        return "Usage: note <id> \"<text>\"\nExample: note R-001 \"Confirmed with CTO\""

    item_id = args[0]  # Keep original case for hash-based IDs
    note_text = " ".join(args[1:]).strip('"\'')

    result = session.get_item_by_id(item_id)
    if not result:
        return f"Item not found: {item_id}"

    item_type, item = result

    # Add note to the item (store in reasoning field for now)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    if item_type == 'risk':
        if not hasattr(item, 'notes') or item.notes is None:
            item.notes = []
        if not isinstance(getattr(item, 'notes', None), list):
            item.notes = []
        item.notes.append({"text": note_text, "timestamp": timestamp})

        # Also append to reasoning for persistence
        old_reasoning = item.reasoning
        item.reasoning = f"{old_reasoning}\n\n[Note {timestamp}]: {note_text}"
        session.record_modification(item_type, item_id, 'reasoning', old_reasoning, item.reasoning)
        return f"✓ Added note to {item_id}: \"{note_text}\""

    elif item_type == 'work_item':
        old_reasoning = item.reasoning
        item.reasoning = f"{old_reasoning}\n\n[Note {timestamp}]: {note_text}"
        session.record_modification(item_type, item_id, 'reasoning', old_reasoning, item.reasoning)
        return f"✓ Added note to {item_id}: \"{note_text}\""

    elif item_type == 'fact':
        old_evidence = item.evidence or {}
        notes = old_evidence.get('notes', [])
        notes.append({"text": note_text, "timestamp": timestamp})
        item.evidence = {**old_evidence, 'notes': notes}
        return f"✓ Added note to {item_id}: \"{note_text}\""

    return f"Cannot add notes to items of type '{item_type}'"


def cmd_search(session: Session, args: List[str]) -> str:
    """Search across all items."""
    if not args:
        return "Usage: search \"<query>\"\nExample: search \"VMware\""

    query = " ".join(args).strip('"\'').lower()
    results = []

    # Search facts
    for fact in session.fact_store.facts:
        if query in fact.item.lower() or query in str(fact.details).lower():
            results.append(f"  {fact.fact_id} [fact]: {fact.item[:60]}...")

    # Search gaps
    for gap in session.fact_store.gaps:
        if query in gap.description.lower():
            results.append(f"  {gap.gap_id} [gap]: {gap.description[:60]}...")

    # Search risks
    for risk in session.reasoning_store.risks:
        if query in risk.title.lower() or query in risk.description.lower():
            results.append(f"  {risk.finding_id} [risk/{risk.severity}]: {risk.title}")

    # Search work items
    for wi in session.reasoning_store.work_items:
        if query in wi.title.lower() or query in wi.description.lower():
            results.append(f"  {wi.finding_id} [work-item/{wi.phase}]: {wi.title}")

    # Search strategic considerations
    for sc in session.reasoning_store.strategic_considerations:
        if query in sc.title.lower() or query in sc.description.lower():
            results.append(f"  {sc.finding_id} [strategic]: {sc.title}")

    # Search recommendations
    for rec in session.reasoning_store.recommendations:
        if query in rec.title.lower() or query in rec.description.lower():
            results.append(f"  {rec.finding_id} [recommendation]: {rec.title}")

    if not results:
        return f"No results found for: \"{query}\""

    output = [f"\nSearch results for \"{query}\" ({len(results)} matches):", "=" * 50]
    output.extend(results)

    return "\n".join(output)


def cmd_history(session: Session, args: List[str]) -> str:
    """Show modification history."""
    if not session.modifications:
        return "No modifications recorded."

    output = ["\nModification History:", "=" * 50]

    for i, mod in enumerate(session.modifications, 1):
        output.append(f"\n{i}. [{mod.timestamp}]")
        output.append(f"   {mod.item_type.upper()} {mod.item_id}: {mod.field}")
        output.append(f"   {mod.old_value} → {mod.new_value}")

    saved_marker = session._last_save_modification_count
    if saved_marker > 0:
        output.append(f"\n[Saved at modification #{saved_marker}]")

    if session.has_unsaved_changes:
        output.append(f"\n⚠ {session.unsaved_change_count} unsaved change(s)")

    return "\n".join(output)


def cmd_rerun(session: Session, args: List[str]) -> str:
    """Re-run reasoning on a domain (uses API)."""
    if not args:
        return """
rerun - Re-analyze a domain with the reasoning agent

Usage:
  rerun <domain>       Re-run reasoning for a specific domain
  rerun all            Re-run reasoning for all domains

Domains: infrastructure, network, cybersecurity, applications, identity_access, organization

Note: This will use API credits. You'll be asked to confirm before running.

Example:
  rerun infrastructure
  rerun cybersecurity
"""

    domain = args[0].lower()

    if domain == 'all':
        domains_to_run = VALID_DOMAINS
    elif domain in VALID_DOMAINS:
        domains_to_run = [domain]
    else:
        return f"Invalid domain: {domain}\nValid domains: {', '.join(VALID_DOMAINS)}, all"

    # Show what will happen
    output = []
    output.append("")
    output.append("=" * 50)
    output.append("  RE-RUN REASONING")
    output.append("=" * 50)
    output.append("")
    output.append(f"  Domains to analyze: {', '.join(domains_to_run)}")
    output.append("")
    output.append("  This will:")
    output.append("  1. Use existing facts from the session")
    output.append("  2. Run reasoning agent(s) to generate new findings")
    output.append("  3. Replace current risks/work items for those domains")
    output.append("")

    # Show current deal context if set
    if session.deal_context and session.deal_context.get('notes'):
        output.append("  Deal context will be included:")
        for note in session.deal_context['notes'][:3]:
            output.append(f"    - {note['text'][:50]}...")
        output.append("")

    output.append("  Estimated cost: ~$0.05-0.15 per domain")
    output.append("")
    output.append("  " + "-" * 40)
    output.append("  To proceed, use: rerun --confirm " + domain)
    output.append("  " + "-" * 40)

    return "\n".join(output)


def cmd_rerun_confirm(session: Session, domain: str) -> str:
    """Actually execute the rerun (called after confirmation)."""
    # This would integrate with the actual reasoning agents
    # For now, return a placeholder that explains what would happen

    return f"""
Re-run functionality is ready but requires integration with main_v2.py.

To re-run analysis with new context:
  1. Export your changes: export
  2. Run: python main_v2.py --from-facts <facts_file> --deal-context <context_file>

This will:
  - Load your existing facts
  - Apply your deal context
  - Re-run reasoning with new context
  - Generate updated findings

Future: Direct re-run from interactive mode (coming soon)
"""


def cmd_compare(session: Session, args: List[str]) -> str:
    """Compare current session to a previous export."""
    if not args:
        return """
compare - Compare current findings to a previous run

Usage:
  compare <findings_file>    Compare to a previous findings file

Example:
  compare output/findings/findings_20240115_100000.json

Shows:
  - New risks added
  - Risks removed
  - Severity changes
  - New work items
"""

    file_path = Path(args[0])
    if not file_path.exists():
        return f"File not found: {file_path}"

    # Load the comparison file
    try:
        import json
        with open(file_path) as f:
            old_data = json.load(f)
    except Exception as e:
        return f"Error loading file: {e}"

    # Compare risks
    output = []
    output.append("")
    output.append("=" * 50)
    output.append("  COMPARISON")
    output.append("=" * 50)

    old_risks = {r.get('title', ''): r for r in old_data.get('findings', {}).get('risks', [])}
    current_risks = {r.title: r for r in session.reasoning_store.risks}

    # New risks
    new_risks = [t for t in current_risks if t not in old_risks]
    removed_risks = [t for t in old_risks if t not in current_risks]

    output.append("")
    output.append(f"  Current risks:  {len(current_risks)}")
    output.append(f"  Previous risks: {len(old_risks)}")
    output.append("")

    if new_risks:
        output.append("  NEW RISKS:")
        for title in new_risks[:5]:
            risk = current_risks[title]
            output.append(f"    + {risk.finding_id}: {title} ({risk.severity})")
        output.append("")

    if removed_risks:
        output.append("  REMOVED RISKS:")
        for title in removed_risks[:5]:
            output.append(f"    - {title}")
        output.append("")

    # Compare severity changes
    changed = []
    for title in current_risks:
        if title in old_risks:
            old_sev = old_risks[title].get('severity', '')
            new_sev = current_risks[title].severity
            if old_sev != new_sev:
                changed.append((title, old_sev, new_sev))

    if changed:
        output.append("  SEVERITY CHANGES:")
        for title, old_sev, new_sev in changed[:5]:
            output.append(f"    {title}: {old_sev} -> {new_sev}")
        output.append("")

    if not new_risks and not removed_risks and not changed:
        output.append("  No significant changes detected.")

    return "\n".join(output)


# Command registry
COMMANDS: Dict[str, Callable[[Session, List[str]], str]] = {
    'help': cmd_help,
    'status': cmd_status,
    'list': cmd_list,
    'explain': cmd_explain,
    'adjust': cmd_adjust,
    'undo': cmd_undo,
    'add': cmd_add,
    'clear': cmd_clear,
    'show': cmd_show,
    'export': cmd_export,
    'delete': cmd_delete,
    'note': cmd_note,
    'search': cmd_search,
    'history': cmd_history,
    'rerun': cmd_rerun,
    'compare': cmd_compare,
}
