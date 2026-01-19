"""
Narrative Synthesis Agent

Transforms domain findings and function stories into cohesive executive narratives.
This is the "story layer" that makes analysis IC-ready.

Input: All domain findings, function stories, deal context
Output: ExecutiveNarrative with all 6 sections
"""

import anthropic
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime
from time import time

from prompts.v2_narrative_synthesis_prompt import (
    ExecutiveNarrative,
    NARRATIVE_SYNTHESIS_PROMPT,
    get_synthesis_prompt,
    get_deal_type_emphasis,
    validate_narrative,
    create_empty_narrative
)

# Import deal-type templates
try:
    from prompts.templates import (
        DealType,
        get_template_for_deal_type,
        get_executive_summary_framing,
        validate_narrative_for_deal_type,
        DEAL_TYPE_CONFIGS
    )
    TEMPLATES_AVAILABLE = True
except ImportError:
    TEMPLATES_AVAILABLE = False
    DealType = None

# Import rate limiter if available
try:
    from config_v2 import (
        estimate_cost,
        API_RATE_LIMIT_SEMAPHORE_SIZE,
        API_RATE_LIMIT_PER_MINUTE
    )
    from tools_v2.rate_limiter import APIRateLimiter
except ImportError:
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        return 0.0
    APIRateLimiter = None


logger = logging.getLogger(__name__)


class NarrativeSynthesisAgent:
    """
    Agent that synthesizes domain findings into executive narratives.

    This agent:
    1. Takes all findings from reasoning agents
    2. Takes function stories
    3. Produces a structured ExecutiveNarrative
    4. Validates output against L3 expectations
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 16384  # Narratives can be long
    ):
        if not api_key:
            raise ValueError("API key must be provided")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.logger = logging.getLogger("narrative_synthesis")

        # Metrics
        self.metrics = {
            "api_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost": 0.0,
            "execution_time": 0.0
        }

    def synthesize(
        self,
        deal_context: Dict,
        domain_findings: Dict,
        function_stories: List[Dict],
        facts_summary: str
    ) -> Dict[str, Any]:
        """
        Synthesize all inputs into an executive narrative.

        Args:
            deal_context: Deal metadata (company_name, deal_type, etc.)
            domain_findings: Findings from all domain reasoning agents
            function_stories: Function stories from reasoning phase
            facts_summary: Summary of facts inventory

        Returns:
            Dict with narrative, validation results, and metrics
        """
        start_time = time()
        company_name = deal_context.get('company_name', 'Target Company')
        deal_type = deal_context.get('deal_type', 'acquisition')

        self.logger.info(f"Starting narrative synthesis for {company_name} ({deal_type})")
        print(f"\n{'='*60}")
        print(f"Narrative Synthesis: {company_name}")
        print(f"Deal Type: {deal_type}")
        print(f"{'='*60}")

        try:
            # Get deal-type-specific template if available
            template_info = None
            if TEMPLATES_AVAILABLE:
                template_info = get_template_for_deal_type(deal_type)
                self.logger.info(f"Using {deal_type} template with emphasis: {template_info['emphasis'].get('primary_lenses', [])}")
                print(f"Template: {deal_type.upper()} (primary focus: {', '.join(template_info['emphasis'].get('primary_lenses', []))})")

            # Build the synthesis prompt
            prompt = get_synthesis_prompt(
                deal_context=deal_context,
                domain_findings=domain_findings,
                function_stories=function_stories,
                facts_summary=facts_summary
            )

            # Add deal-type-specific prompt additions
            if template_info and template_info.get('prompt_additions'):
                prompt = prompt + "\n\n" + template_info['prompt_additions']

            # Get deal-type emphasis
            emphasis = get_deal_type_emphasis(deal_type)
            self.logger.debug(f"Deal emphasis: {emphasis}")

            # Call the API
            print("Generating narrative...")
            response = self._call_api(prompt)

            # Parse the response into structured narrative
            narrative = self._parse_narrative_response(
                response,
                company_name,
                deal_type
            )

            # Validate the narrative (base validation)
            validation = validate_narrative(narrative)

            # Add deal-type-specific validation if templates available
            deal_type_validation = None
            if TEMPLATES_AVAILABLE:
                deal_type_validation = validate_narrative_for_deal_type(
                    narrative.to_dict(),
                    deal_type
                )
                # Merge deal-type issues into main validation
                validation['deal_type_issues'] = deal_type_validation.get('issues', [])
                validation['deal_type_warnings'] = deal_type_validation.get('warnings', [])
                validation['deal_type_score'] = deal_type_validation.get('score', 0)

            # Calculate execution time
            self.metrics["execution_time"] = time() - start_time

            print(f"\nNarrative generated in {self.metrics['execution_time']:.1f}s")
            print(f"Validation: {'PASS' if validation['valid'] else 'ISSUES FOUND'}")
            if validation['issues']:
                for issue in validation['issues']:
                    print(f"  - {issue}")
            if deal_type_validation and deal_type_validation.get('issues'):
                print(f"Deal-type validation ({deal_type}):")
                for issue in deal_type_validation['issues']:
                    print(f"  - {issue}")

            return {
                "status": "success",
                "narrative": narrative.to_dict(),
                "narrative_markdown": narrative.to_markdown(),
                "validation": validation,
                "deal_type_validation": deal_type_validation,
                "template_used": deal_type if TEMPLATES_AVAILABLE else None,
                "metrics": self.metrics
            }

        except Exception as e:
            self.logger.error(f"Narrative synthesis failed: {e}")
            self.metrics["execution_time"] = time() - start_time
            return {
                "status": "error",
                "error": str(e),
                "metrics": self.metrics
            }

    def _call_api(self, prompt: str) -> str:
        """Make API call and track metrics."""
        self.metrics["api_calls"] += 1

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0.3,  # Slight creativity for narrative writing
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Track tokens
        self.metrics["input_tokens"] += response.usage.input_tokens
        self.metrics["output_tokens"] += response.usage.output_tokens
        self.metrics["estimated_cost"] += estimate_cost(
            self.model,
            response.usage.input_tokens,
            response.usage.output_tokens
        )

        # Extract text response
        return response.content[0].text

    def _parse_narrative_response(
        self,
        response: str,
        company_name: str,
        deal_type: str
    ) -> ExecutiveNarrative:
        """Parse the LLM response into structured ExecutiveNarrative."""
        narrative = create_empty_narrative(company_name, deal_type)

        # Parse each section from the response
        sections = self._split_sections(response)

        # Section 1: Executive Summary
        if "executive summary" in sections:
            narrative.executive_summary = self._parse_bullets(sections["executive summary"])

        # Section 2: Organization Structure
        if "organization" in sections:
            narrative.org_structure_narrative = sections["organization"].strip()

        # Section 3: Team Stories
        if "team" in sections:
            narrative.team_stories = self._parse_team_stories(sections["team"])

        # Section 4: M&A Lens
        if "m&a lens" in sections or "mna lens" in sections:
            mna_content = sections.get("m&a lens", sections.get("mna lens", ""))
            narrative.mna_lens_section = self._parse_mna_section(mna_content)

        # Section 5: Benchmarks
        if "benchmark" in sections:
            narrative.benchmark_statements = self._parse_bullets(sections["benchmark"])

        # Section 6: Risks and Synergies
        if "risk" in sections:
            narrative.risks_table = self._parse_table(sections["risk"],
                ["risk", "why_it_matters", "likely_impact", "mitigation"])

        if "synerg" in sections:
            narrative.synergies_table = self._parse_table(sections["synerg"],
                ["opportunity", "why_it_matters", "value_mechanism", "first_step"])

        return narrative

    def _split_sections(self, response: str) -> Dict[str, str]:
        """Split response into sections by headers."""
        sections = {}
        current_section = None
        current_content = []

        for line in response.split('\n'):
            # Check for section headers (## or ### followed by number or keyword)
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                    current_content = []

                # Identify new section
                header_lower = line.lower()
                if 'executive summary' in header_lower or '1)' in header_lower:
                    current_section = 'executive summary'
                elif 'organization' in header_lower or 'built' in header_lower or '2)' in header_lower:
                    current_section = 'organization'
                elif 'team' in header_lower or '3)' in header_lower:
                    current_section = 'team'
                elif 'm&a lens' in header_lower or 'mna' in header_lower or '4)' in header_lower:
                    current_section = 'm&a lens'
                elif 'benchmark' in header_lower or '5)' in header_lower:
                    current_section = 'benchmark'
                elif 'risk' in header_lower and 'synerg' in header_lower or '6)' in header_lower:
                    current_section = 'risk'
                elif 'synerg' in header_lower:
                    current_section = 'synerg'
                elif 'risk' in header_lower:
                    current_section = 'risk'
                else:
                    current_section = header_lower.strip('#').strip()
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _parse_bullets(self, content: str) -> List[str]:
        """Parse bullet points from content."""
        bullets = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* ') or line.startswith('• '):
                bullets.append(line[2:].strip())
            elif line.startswith('-') or line.startswith('*'):
                bullets.append(line[1:].strip())
        return bullets

    def _parse_team_stories(self, content: str) -> List[Dict]:
        """Parse team stories from content."""
        stories = []
        current_story = None

        for line in content.split('\n'):
            line = line.strip()

            # New team/function header
            if line.startswith('###') or (line.startswith('**') and line.endswith('**')):
                if current_story:
                    stories.append(current_story)
                function_name = line.strip('#').strip('*').strip()
                current_story = {
                    'function_name': function_name,
                    'day_to_day': '',
                    'strengths': [],
                    'constraints': [],
                    'upstream_dependencies': [],
                    'downstream_dependents': [],
                    'mna_implication': ''
                }

            elif current_story:
                line_lower = line.lower()

                if 'day-to-day' in line_lower or 'what they do' in line_lower:
                    # Extract content after the label
                    if ':' in line:
                        current_story['day_to_day'] = line.split(':', 1)[1].strip().strip('*')

                elif 'do well' in line_lower or 'strength' in line_lower:
                    pass  # Next lines will be strengths

                elif 'constrain' in line_lower or 'bottleneck' in line_lower:
                    pass  # Next lines will be constraints

                elif 'upstream' in line_lower:
                    if ':' in line:
                        deps = line.split(':', 1)[1].strip()
                        current_story['upstream_dependencies'] = [d.strip() for d in deps.split(',')]

                elif 'downstream' in line_lower:
                    if ':' in line:
                        deps = line.split(':', 1)[1].strip()
                        current_story['downstream_dependents'] = [d.strip() for d in deps.split(',')]

                elif 'm&a implication' in line_lower or 'mna implication' in line_lower:
                    if ':' in line:
                        current_story['mna_implication'] = line.split(':', 1)[1].strip().strip('*')

                elif line.startswith('- ') or line.startswith('* '):
                    bullet = line[2:].strip()
                    # Determine if strength or constraint based on recent context
                    if any(word in bullet.lower() for word in ['risk', 'gap', 'constraint', 'limit', 'concern', 'weak']):
                        current_story['constraints'].append(bullet)
                    elif bullet:
                        current_story['strengths'].append(bullet)

        # Add last story
        if current_story:
            stories.append(current_story)

        return stories

    def _parse_mna_section(self, content: str) -> Dict[str, List[str]]:
        """Parse M&A lens section."""
        result = {
            "tsa_exposed_functions": [],
            "day_1_requirements": [],
            "separation_considerations": []
        }

        current_list = None
        for line in content.split('\n'):
            line = line.strip()
            line_lower = line.lower()

            if 'tsa' in line_lower and ('exposed' in line_lower or 'function' in line_lower):
                current_list = 'tsa_exposed_functions'
            elif 'day-1' in line_lower or 'day 1' in line_lower:
                current_list = 'day_1_requirements'
            elif 'separation' in line_lower:
                current_list = 'separation_considerations'
            elif (line.startswith('- ') or line.startswith('* ')) and current_list:
                result[current_list].append(line[2:].strip())

        return result

    def _parse_table(self, content: str, columns: List[str]) -> List[Dict]:
        """Parse markdown table into list of dicts."""
        rows = []
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('|') and '---' not in line:
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) >= len(columns) and cells[0]:
                    # Skip header row
                    if cells[0].lower() != columns[0].replace('_', ' '):
                        row = {}
                        for i, col in enumerate(columns):
                            row[col] = cells[i] if i < len(cells) else ''
                        rows.append(row)

        return rows

    def synthesize_quick(
        self,
        reasoning_store,
        deal_context: Dict,
        fact_store=None
    ) -> Dict[str, Any]:
        """
        Quick synthesis from ReasoningStore and FactStore.

        Convenience method that extracts data from stores.
        """
        # Get all findings
        findings = reasoning_store.get_all_findings()

        # Get function stories
        function_stories = findings.get('function_stories', [])

        # Build domain findings structure
        domain_findings = {
            "risks": findings.get('risks', []),
            "strategic_considerations": findings.get('strategic_considerations', []),
            "work_items": findings.get('work_items', []),
            "recommendations": findings.get('recommendations', [])
        }

        # Build facts summary
        if fact_store:
            facts_data = fact_store.get_all_facts()
            facts_summary = f"Total facts: {facts_data['summary']['total_facts']}, Gaps: {facts_data['summary']['total_gaps']}"
        else:
            facts_summary = "Facts summary not available"

        return self.synthesize(
            deal_context=deal_context,
            domain_findings=domain_findings,
            function_stories=function_stories,
            facts_summary=facts_summary
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_narrative_agent(api_key: str, model: str = None) -> NarrativeSynthesisAgent:
    """Factory function to create narrative synthesis agent."""
    return NarrativeSynthesisAgent(
        api_key=api_key,
        model=model or "claude-sonnet-4-20250514"
    )


__all__ = [
    'NarrativeSynthesisAgent',
    'create_narrative_agent'
]
