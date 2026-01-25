"""
Incremental Fact Extractor

Extracts facts from new/updated documents with context awareness:
- Knows what facts already exist to avoid duplicates
- Extracts evidence with exact quotes and page numbers
- Assigns confidence scores
- Detects domains and categories from content

Phase 2 Steps 24-33
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class FactDomain(Enum):
    """Domains for extracted facts."""
    INFRASTRUCTURE = "infrastructure"
    APPLICATIONS = "applications"
    SECURITY = "security"
    DATA = "data"
    ORGANIZATION = "organization"
    COMPLIANCE = "compliance"
    VENDORS = "vendors"
    CONTRACTS = "contracts"
    UNKNOWN = "unknown"


@dataclass
class ExtractedEvidence:
    """Evidence supporting an extracted fact."""
    exact_quote: str
    page_number: int = 0
    section: str = ""
    context: str = ""  # Surrounding text for context


@dataclass
class ExtractedFact:
    """A fact extracted from a document."""
    # Core identification
    temp_id: str = ""  # Temporary ID until merged
    domain: str = ""
    category: str = ""
    item: str = ""
    status: str = ""

    # Details
    details: Dict[str, Any] = field(default_factory=dict)

    # Evidence
    evidence: ExtractedEvidence = None

    # Confidence and source
    confidence_score: float = 0.0
    confidence_reasons: List[str] = field(default_factory=list)
    source_document: str = ""
    extracted_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "temp_id": self.temp_id,
            "domain": self.domain,
            "category": self.category,
            "item": self.item,
            "status": self.status,
            "details": self.details,
            "evidence": {
                "exact_quote": self.evidence.exact_quote if self.evidence else "",
                "page_number": self.evidence.page_number if self.evidence else 0,
                "section": self.evidence.section if self.evidence else "",
                "context": self.evidence.context if self.evidence else ""
            },
            "confidence_score": self.confidence_score,
            "confidence_reasons": self.confidence_reasons,
            "source_document": self.source_document,
            "extracted_at": self.extracted_at
        }


@dataclass
class ExtractionContext:
    """Context for extraction including existing facts."""
    existing_facts_summary: str = ""
    existing_domains: List[str] = field(default_factory=list)
    existing_categories: Dict[str, List[str]] = field(default_factory=dict)
    document_type: str = ""
    company_context: str = ""


class IncrementalExtractor:
    """
    Extracts facts from document content with context awareness.

    Features:
    - Domain detection from content patterns
    - Evidence extraction with exact quotes
    - Confidence scoring based on evidence quality
    - Deduplication against existing facts
    """

    # Domain detection patterns
    DOMAIN_PATTERNS = {
        FactDomain.INFRASTRUCTURE: [
            r'\b(server|hardware|network|firewall|switch|router|datacenter|cloud|aws|azure|gcp)\b',
            r'\b(vmware|hypervisor|storage|san|nas|backup)\b',
            r'\b(cpu|memory|ram|disk|bandwidth)\b'
        ],
        FactDomain.APPLICATIONS: [
            r'\b(application|software|system|platform|erp|crm|saas)\b',
            r'\b(database|sql|oracle|mongodb|postgresql)\b',
            r'\b(api|integration|middleware)\b'
        ],
        FactDomain.SECURITY: [
            r'\b(security|firewall|antivirus|encryption|mfa|sso)\b',
            r'\b(vulnerability|penetration|audit|compliance)\b',
            r'\b(access control|authentication|authorization)\b'
        ],
        FactDomain.DATA: [
            r'\b(data|database|warehouse|lake|analytics)\b',
            r'\b(pii|phi|sensitive|confidential)\b',
            r'\b(backup|recovery|replication)\b'
        ],
        FactDomain.ORGANIZATION: [
            r'\b(team|staff|employee|headcount|fte)\b',
            r'\b(department|organization|structure)\b',
            r'\b(role|responsibility|manager)\b'
        ],
        FactDomain.COMPLIANCE: [
            r'\b(soc\s*2|iso\s*27001|hipaa|gdpr|pci|fedramp)\b',
            r'\b(audit|certification|compliance|regulatory)\b',
            r'\b(policy|procedure|control)\b'
        ],
        FactDomain.VENDORS: [
            r'\b(vendor|supplier|partner|contractor)\b',
            r'\b(third.?party|outsource)\b'
        ],
        FactDomain.CONTRACTS: [
            r'\b(contract|agreement|license|subscription)\b',
            r'\b(renewal|expiration|term)\b',
            r'\b(sla|service level)\b'
        ]
    }

    # Category patterns within domains
    CATEGORY_PATTERNS = {
        "infrastructure": {
            "servers": [r'\b(server|host|vm|instance)\b'],
            "network": [r'\b(network|switch|router|firewall|vpn)\b'],
            "storage": [r'\b(storage|san|nas|disk|volume)\b'],
            "cloud": [r'\b(aws|azure|gcp|cloud)\b'],
            "datacenter": [r'\b(datacenter|colo|facility)\b']
        },
        "applications": {
            "enterprise": [r'\b(erp|crm|hcm|finance)\b'],
            "productivity": [r'\b(office|email|collaboration)\b'],
            "development": [r'\b(ide|git|ci.?cd|devops)\b'],
            "database": [r'\b(database|sql|nosql)\b'],
            "custom": [r'\b(custom|proprietary|in-house)\b']
        },
        "security": {
            "identity": [r'\b(identity|iam|sso|mfa|ldap)\b'],
            "endpoint": [r'\b(endpoint|antivirus|edr|mdm)\b'],
            "network_security": [r'\b(firewall|ids|ips|waf)\b'],
            "data_protection": [r'\b(dlp|encryption|key management)\b']
        }
    }

    def __init__(self, fact_store=None):
        self.fact_store = fact_store
        self._temp_id_counter = 0

    def _generate_temp_id(self) -> str:
        """Generate temporary ID for extracted fact."""
        self._temp_id_counter += 1
        return f"EXT-{self._temp_id_counter:04d}"

    def build_context(self) -> ExtractionContext:
        """Build extraction context from existing fact store."""
        context = ExtractionContext()

        if not self.fact_store:
            return context

        # Summarize existing facts
        facts = self.fact_store.facts
        if facts:
            domains = set()
            categories_by_domain = {}

            for fact in facts:
                domains.add(fact.domain)
                if fact.domain not in categories_by_domain:
                    categories_by_domain[fact.domain] = set()
                categories_by_domain[fact.domain].add(fact.category)

            context.existing_domains = list(domains)
            context.existing_categories = {
                d: list(cats) for d, cats in categories_by_domain.items()
            }

            # Create summary string
            summary_parts = []
            for domain in domains:
                count = sum(1 for f in facts if f.domain == domain)
                summary_parts.append(f"{domain}: {count} facts")
            context.existing_facts_summary = "; ".join(summary_parts)

        return context

    def detect_domain(self, text: str) -> Tuple[FactDomain, float]:
        """
        Detect the primary domain of text content.

        Returns:
            Tuple of (domain, confidence)
        """
        text_lower = text.lower()
        domain_scores = {}

        for domain, patterns in self.DOMAIN_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                score += len(matches)
            domain_scores[domain] = score

        if not any(domain_scores.values()):
            return FactDomain.UNKNOWN, 0.0

        best_domain = max(domain_scores, key=domain_scores.get)
        total_score = sum(domain_scores.values())
        confidence = domain_scores[best_domain] / total_score if total_score > 0 else 0.0

        return best_domain, confidence

    def detect_category(self, text: str, domain: str) -> Tuple[str, float]:
        """
        Detect category within a domain.

        Returns:
            Tuple of (category, confidence)
        """
        if domain not in self.CATEGORY_PATTERNS:
            return "general", 0.5

        text_lower = text.lower()
        category_scores = {}

        for category, patterns in self.CATEGORY_PATTERNS[domain].items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                score += len(matches)
            category_scores[category] = score

        if not any(category_scores.values()):
            return "general", 0.5

        best_category = max(category_scores, key=category_scores.get)
        total_score = sum(category_scores.values())
        confidence = category_scores[best_category] / total_score if total_score > 0 else 0.5

        return best_category, confidence

    def extract_evidence(
        self,
        content: str,
        item_text: str,
        page_hint: int = 0
    ) -> Optional[ExtractedEvidence]:
        """
        Extract evidence for a fact from document content.

        Args:
            content: Full document content
            item_text: The fact item to find evidence for
            page_hint: Suggested page number if known

        Returns:
            ExtractedEvidence with exact quote
        """
        # Try to find the item text in the content
        item_lower = item_text.lower()

        # Look for sentences containing key terms
        sentences = re.split(r'[.!?]\s+', content)

        best_match = None
        best_score = 0

        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Score based on term overlap
            item_terms = set(item_lower.split())
            sentence_terms = set(sentence_lower.split())
            overlap = len(item_terms & sentence_terms)

            if overlap > best_score and len(sentence) > 20:
                best_score = overlap
                best_match = sentence.strip()

        if best_match:
            # Try to determine page number from [Page X] markers
            page_number = page_hint
            page_match = re.search(rf'\[Page (\d+)\][^[]*{re.escape(best_match[:50])}',
                                   content, re.IGNORECASE)
            if page_match:
                page_number = int(page_match.group(1))

            return ExtractedEvidence(
                exact_quote=best_match[:500],  # Limit quote length
                page_number=page_number,
                section="",
                context=""
            )

        return None

    def calculate_confidence(
        self,
        fact: ExtractedFact,
        content: str
    ) -> Tuple[float, List[str]]:
        """
        Calculate confidence score for an extracted fact.

        Returns:
            Tuple of (confidence_score, reasons)
        """
        score = 0.5  # Base score
        reasons = []

        # Evidence quality
        if fact.evidence:
            if fact.evidence.exact_quote:
                score += 0.15
                reasons.append("Has exact quote evidence")
            if fact.evidence.page_number > 0:
                score += 0.05
                reasons.append("Has page reference")

        # Detail richness
        if fact.details:
            detail_count = len(fact.details)
            if detail_count >= 3:
                score += 0.1
                reasons.append("Rich details")
            elif detail_count >= 1:
                score += 0.05
                reasons.append("Some details")

        # Status clarity
        if fact.status in ["confirmed", "active", "in_use", "deployed"]:
            score += 0.1
            reasons.append("Clear status")

        # Domain/category clarity
        if fact.domain and fact.domain != "unknown":
            score += 0.05
            reasons.append("Clear domain")

        # Check for duplicates
        if self.fact_store:
            similar = self._find_similar_facts(fact)
            if similar:
                score -= 0.1
                reasons.append("Similar fact exists")

        # Clamp to [0, 1]
        score = max(0.0, min(1.0, score))

        return score, reasons

    def _find_similar_facts(self, fact: ExtractedFact) -> List:
        """Find similar existing facts."""
        if not self.fact_store:
            return []

        similar = []
        for existing in self.fact_store.facts:
            if existing.domain != fact.domain:
                continue

            # Check item similarity
            if self._text_similarity(existing.item, fact.item) > 0.8:
                similar.append(existing)

        return similar

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity."""
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def extract_facts_from_content(
        self,
        content: str,
        source_document: str,
        context: ExtractionContext = None
    ) -> List[ExtractedFact]:
        """
        Extract facts from document content.

        This is a pattern-based extractor. For full LLM-based extraction,
        integrate with the analysis pipeline.

        Args:
            content: Document text content
            source_document: Filename of source
            context: Extraction context with existing facts

        Returns:
            List of extracted facts
        """
        facts = []
        timestamp = datetime.now().isoformat()

        # Detect overall domain
        primary_domain, domain_conf = self.detect_domain(content)

        # Split content into sections for more granular extraction
        sections = self._split_into_sections(content)

        for section in sections:
            # Detect domain for this section
            section_domain, _ = self.detect_domain(section)
            if section_domain == FactDomain.UNKNOWN:
                section_domain = primary_domain

            # Detect category
            category, _ = self.detect_category(section, section_domain.value)

            # Extract potential facts from section
            section_facts = self._extract_from_section(
                section,
                section_domain.value,
                category,
                source_document,
                timestamp
            )

            facts.extend(section_facts)

        # Calculate confidence for all facts
        for fact in facts:
            confidence, reasons = self.calculate_confidence(fact, content)
            fact.confidence_score = confidence
            fact.confidence_reasons = reasons

        # Deduplicate within this extraction
        facts = self._deduplicate_facts(facts)

        logger.info(f"Extracted {len(facts)} facts from {source_document}")
        return facts

    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections."""
        sections = []

        # Try splitting by page markers
        if "[Page " in content:
            pages = content.split("[Page ")
            for page in pages:
                if page.strip():
                    sections.append(page)
        else:
            # Split by double newlines or headers
            parts = re.split(r'\n\n+|\n#{1,3}\s+', content)
            sections = [p.strip() for p in parts if len(p.strip()) > 100]

        # If no good sections, use whole content
        if not sections:
            sections = [content]

        return sections

    def _extract_from_section(
        self,
        section: str,
        domain: str,
        category: str,
        source_document: str,
        timestamp: str
    ) -> List[ExtractedFact]:
        """Extract facts from a single section using pattern matching."""
        facts = []

        # Extract list items (common in IT documentation)
        list_items = re.findall(r'^[\s]*[-•*]\s*(.+)$', section, re.MULTILINE)
        for item in list_items:
            if len(item) > 10 and len(item) < 200:
                fact = self._create_fact_from_item(
                    item, domain, category, section, source_document, timestamp
                )
                if fact:
                    facts.append(fact)

        # Extract table-like data
        table_rows = re.findall(r'^(.+?)\s*[:|]\s*(.+)$', section, re.MULTILINE)
        for key, value in table_rows:
            if len(key) > 3 and len(value) > 3:
                fact = self._create_fact_from_kv(
                    key.strip(), value.strip(), domain, category,
                    section, source_document, timestamp
                )
                if fact:
                    facts.append(fact)

        return facts

    def _create_fact_from_item(
        self,
        item: str,
        domain: str,
        category: str,
        section: str,
        source_document: str,
        timestamp: str
    ) -> Optional[ExtractedFact]:
        """Create a fact from a list item."""
        # Skip generic items
        if item.lower() in ['n/a', 'none', 'tbd', 'unknown']:
            return None

        evidence = self.extract_evidence(section, item)

        return ExtractedFact(
            temp_id=self._generate_temp_id(),
            domain=domain,
            category=category,
            item=item,
            status="extracted",
            details={},
            evidence=evidence,
            source_document=source_document,
            extracted_at=timestamp
        )

    def _create_fact_from_kv(
        self,
        key: str,
        value: str,
        domain: str,
        category: str,
        section: str,
        source_document: str,
        timestamp: str
    ) -> Optional[ExtractedFact]:
        """Create a fact from a key-value pair."""
        # Skip generic entries
        if value.lower() in ['n/a', 'none', 'tbd', 'unknown', '']:
            return None

        evidence = self.extract_evidence(section, f"{key}: {value}")

        return ExtractedFact(
            temp_id=self._generate_temp_id(),
            domain=domain,
            category=category,
            item=key,
            status="confirmed",
            details={key.lower().replace(' ', '_'): value},
            evidence=evidence,
            source_document=source_document,
            extracted_at=timestamp
        )

    def _deduplicate_facts(self, facts: List[ExtractedFact]) -> List[ExtractedFact]:
        """Remove duplicate facts from list."""
        seen = set()
        unique = []

        for fact in facts:
            # Create signature for deduplication
            sig = f"{fact.domain}:{fact.category}:{fact.item.lower()}"
            if sig not in seen:
                seen.add(sig)
                unique.append(fact)

        return unique
