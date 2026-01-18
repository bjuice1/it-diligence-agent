"""
Coordinator Agent

Synthesizes findings across all domain agents:
- Cross-domain dependencies
- Priority ranking
- Timeline and sequencing
- Executive summary generation
"""
from typing import Dict
from agents.base_agent import BaseAgent
from prompts.coordinator_prompt import COORDINATOR_SYSTEM_PROMPT
from tools.analysis_tools import COORDINATOR_TOOLS


class CoordinatorAgent(BaseAgent):
    """
    Coordinates and synthesizes findings from domain agents.
    
    Responsibilities:
    1. Review all domain findings
    2. Identify cross-domain dependencies
    3. Prioritize risks and work items
    4. Create overall timeline
    5. Generate executive summary
    """
    
    def __init__(self, analysis_store):
        super().__init__(analysis_store)
        self.tools = COORDINATOR_TOOLS  # Extended tool set
    
    @property
    def domain(self) -> str:
        return "cross-domain"
    
    @property
    def system_prompt(self) -> str:
        return COORDINATOR_SYSTEM_PROMPT
    
    def synthesize(self, document_text: str, deal_context: Dict = None) -> Dict:
        """
        Run synthesis after domain agents have completed.
        
        Different from analyze() - this reviews existing findings
        rather than analyzing documents directly.
        """
        print(f"\n{'='*60}")
        print(f"🎯 Starting COORDINATOR Synthesis")
        print(f"{'='*60}")
        
        # Build synthesis message with all domain findings
        user_message = self._build_synthesis_message(document_text, deal_context)
        self.messages = [{"role": "user", "content": user_message}]
        
        # Run agentic loop
        iteration = 0
        while not self.analysis_complete and iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- Synthesis Iteration {iteration} ---")
            
            response = self._call_model()
            self._process_response(response)
            
            if self.analysis_complete:
                print(f"\n✓ Coordination complete after {iteration} iterations")
                break
        
        # Validate synthesis
        validation = self._validate_synthesis()
        if not validation["valid"]:
            self.logger.warning(f"Synthesis validation issues: {validation['issues']}")
            if validation['issues']:
                print(f"\n⚠️  Synthesis validation issues: {', '.join(validation['issues'])}")
        
        return self.store.get_all()
    
    def _format_domain_summary(self, domain: str, findings: Dict) -> str:
        """Format domain findings consistently"""
        lines = [
            f"### {domain.title()} Domain",
            f"Assumptions: {len(findings['assumptions'])}",
            f"Gaps: {len(findings['gaps'])}",
            f"Risks: {len(findings['risks'])}",
            f"Work Items: {len(findings['work_items'])}"
        ]
        
        if findings['summary']:
            summary = findings['summary']
            lines.extend([
                f"Summary: {summary.get('summary', 'N/A')}",
                f"Complexity: {summary.get('complexity_assessment', 'N/A')}",
                f"Cost Range: {summary.get('estimated_cost_range', 'N/A')}"
            ])
        
        lines.append("")
        lines.append("Key risks:")
        for risk in findings['risks'][:5]:
            lines.append(f"- [{risk.get('severity', 'N/A')}] {risk.get('risk', 'N/A')}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _build_synthesis_message(self, document_text: str, deal_context: Dict = None) -> str:
        """Build message with all domain findings for synthesis"""
        import json
        from config import DOMAINS
        
        parts = []
        
        if deal_context:
            parts.append("## Deal Context")
            parts.append(json.dumps(deal_context, indent=2))
            parts.append("")
        
        parts.append("## Original Documents (Reference)")
        parts.append(document_text[:5000] + "..." if len(document_text) > 5000 else document_text)
        parts.append("")
        
        parts.append("## Domain Analysis Findings")
        parts.append("")
        
        # Dynamically build domain summaries
        for domain in DOMAINS:
            findings = self.store.get_by_domain(domain)
            parts.append(self._format_domain_summary(domain, findings))
        
        # All findings detail
        parts.append("## Detailed Findings")
        parts.append("")
        parts.append("### All Assumptions")
        for a in self.store.assumptions:
            # Handle both 'assumption' and 'assumption_text' keys
            assumption_text = a.get('assumption') or a.get('assumption_text', 'N/A')
            parts.append(f"- [{a.get('id', 'N/A')}] [{a.get('domain', 'N/A')}] {assumption_text}")
        parts.append("")
        
        parts.append("### All Gaps")
        for g in self.store.gaps:
            parts.append(f"- [{g['id']}] [{g['domain']}] [{g['priority']}] {g['gap']}")
        parts.append("")
        
        parts.append("### All Risks")
        for r in self.store.risks:
            parts.append(f"- [{r['id']}] [{r['domain']}] [{r['severity']}] {r['risk']}")
        parts.append("")
        
        parts.append("### All Work Items")
        for w in self.store.work_items:
            parts.append(f"- [{w['id']}] [{w['domain']}] {w['title']} - {w.get('effort_estimate', 'N/A')}")
        parts.append("")
        
        parts.append("## Your Task")
        parts.append("1. Identify cross-domain dependencies that affect sequencing")
        parts.append("2. Add any additional risks or work items discovered through synthesis")
        parts.append("3. Create strategic recommendations for the deal team")
        parts.append("4. Generate the executive summary with overall assessment")
        parts.append("5. Call complete_analysis when synthesis is complete")
        
        return "\n".join(parts)
    
    def _validate_synthesis(self) -> Dict:
        """Validate that synthesis is complete"""
        issues = []
        
        # Check executive summary exists
        exec_summary = [r for r in self.store.recommendations 
                       if r.get('domain') == 'deal']
        if not exec_summary:
            issues.append("No executive summary generated")
        
        # Check cross-domain dependencies identified
        cross_deps = [r for r in self.store.risks 
                     if r.get('domain') == 'cross-domain']
        if len(cross_deps) < 2:
            issues.append("Few cross-domain risks identified - may be incomplete")
        
        return {"valid": len(issues) == 0, "issues": issues}
