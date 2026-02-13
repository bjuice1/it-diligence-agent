#!/usr/bin/env python3
"""
Validation Script for IT Due Diligence Automation

Compares automation output against expected facts ground truth to measure accuracy.
Detects known failure modes and validates entity scoping, fact counts, and reasoning outputs.

Usage:
    python validate_automation.py --facts output/facts/facts_TIMESTAMP.json --deal-id <deal_id>
    python validate_automation.py --json-dir output/ --deal-id <deal_id> --verbose
    python validate_automation.py --db data/diligence.db --deal-id <deal_id> --domain organization

Exit codes:
    0 = All validations pass
    1 = Critical failures detected
    2 = Warnings only (no hard failures)
"""

import argparse
import json
import re
import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

# Terminal colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class GroundTruthParser:
    """Parses expected facts from EXPECTED_FACTS_GROUND_TRUTH.md"""

    def __init__(self, ground_truth_path: str):
        self.path = Path(ground_truth_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Ground truth file not found: {ground_truth_path}")

        self.content = self.path.read_text()
        self.expected_counts = self._parse_expected_counts()

    def _parse_expected_counts(self) -> Dict[str, Dict[str, int]]:
        """
        Extract expected fact counts from the summary table.

        Returns:
            {
                "organization": {"target": 15, "buyer": 9, "total": 24},
                "applications": {"target": 38, "buyer": 9, "total": 47},
                ...
            }
        """
        counts = {}

        # Pattern: | **DOMAIN** | target_count | buyer_count | total_count |
        # Example: | **ORGANIZATION** | 15 | 9 | 24 |
        pattern = r'\|\s+\*\*([A-Z_]+)\*\*\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|'

        matches = re.finditer(pattern, self.content)

        for match in matches:
            domain = match.group(1).lower()
            target_count = int(match.group(2))
            buyer_count = int(match.group(3))
            total_count = int(match.group(4))

            counts[domain] = {
                "target": target_count,
                "buyer": buyer_count,
                "total": total_count
            }

        # Special handling for TOTAL row if present
        if "total" in counts:
            counts["_total"] = counts.pop("total")

        return counts

    def get_expected(self, domain: str, entity: Optional[str] = None) -> int:
        """Get expected count for domain and entity"""
        domain = domain.lower()

        if domain not in self.expected_counts:
            return 0

        if entity:
            return self.expected_counts[domain].get(entity.lower(), 0)
        else:
            return self.expected_counts[domain].get("total", 0)

    def get_all_domains(self) -> List[str]:
        """Get list of all domains with expected counts"""
        return [d for d in self.expected_counts.keys() if not d.startswith("_")]


class AutomationOutputLoader:
    """Loads automation output from various sources (JSON, database)"""

    def __init__(self):
        self.facts = {}
        self.inventory = {}
        self.findings = {}

    def load_facts(self, json_path: str) -> Dict:
        """Load facts from JSON file"""
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Facts JSON not found: {json_path}")

        with open(path, 'r') as f:
            data = json.load(f)

        # Group facts by domain and entity
        facts_by_domain = defaultdict(lambda: {"target": 0, "buyer": 0, "total": 0})

        # Handle different JSON structures
        if isinstance(data, dict) and "facts" in data:
            facts_list = data["facts"]
        elif isinstance(data, list):
            facts_list = data
        else:
            facts_list = []

        for fact in facts_list:
            domain = fact.get("domain", "unknown").lower()
            entity = fact.get("entity", "target").lower()

            facts_by_domain[domain][entity] += 1
            facts_by_domain[domain]["total"] += 1

        self.facts = dict(facts_by_domain)
        return self.facts

    def load_inventory(self, deal_id: str, db_path: str) -> Dict:
        """Load inventory items from database"""
        path = Path(db_path)
        if not path.exists():
            print(f"Warning: Database not found at {db_path}, skipping inventory validation")
            return {}

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query inventory items grouped by type and entity
        query = """
            SELECT type, entity, COUNT(*) as count
            FROM inventory_items
            WHERE deal_id = ?
            GROUP BY type, entity
        """

        try:
            cursor.execute(query, (deal_id,))
            rows = cursor.fetchall()

            inventory_by_type = defaultdict(lambda: {"target": 0, "buyer": 0, "total": 0})

            for row in rows:
                item_type, entity, count = row
                entity = (entity or "target").lower()

                inventory_by_type[item_type][entity] += count
                inventory_by_type[item_type]["total"] += count

            self.inventory = dict(inventory_by_type)

        except sqlite3.OperationalError as e:
            print(f"Warning: Could not query inventory: {e}")
            self.inventory = {}
        finally:
            conn.close()

        return self.inventory

    def load_findings(self, deal_id: str, db_path: str) -> Dict:
        """Load findings/reasoning outputs from database"""
        path = Path(db_path)
        if not path.exists():
            print(f"Warning: Database not found at {db_path}, skipping findings validation")
            return {}

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query findings grouped by type and severity/phase
        query = """
            SELECT finding_type, severity, phase, entity, COUNT(*) as count
            FROM findings
            WHERE deal_id = ?
            GROUP BY finding_type, severity, phase, entity
        """

        try:
            cursor.execute(query, (deal_id,))
            rows = cursor.fetchall()

            findings = {
                "risks": {"count": 0, "by_severity": defaultdict(int)},
                "work_items": {"count": 0, "by_phase": defaultdict(int)},
                "recommendations": {"count": 0},
                "strategic_considerations": {"count": 0},
                "total": 0
            }

            for row in rows:
                finding_type, severity, phase, entity, count = row

                findings["total"] += count

                if finding_type == "risk":
                    findings["risks"]["count"] += count
                    if severity:
                        findings["risks"]["by_severity"][severity] += count
                elif finding_type == "work_item":
                    findings["work_items"]["count"] += count
                    if phase:
                        findings["work_items"]["by_phase"][phase] += count
                elif finding_type == "recommendation":
                    findings["recommendations"]["count"] += count
                elif finding_type == "strategic_consideration":
                    findings["strategic_considerations"]["count"] += count

            self.findings = findings

        except sqlite3.OperationalError as e:
            print(f"Warning: Could not query findings: {e}")
            self.findings = {}
        finally:
            conn.close()

        return self.findings


class Validator:
    """Validates automation output against expected ground truth"""

    def __init__(self, ground_truth: GroundTruthParser, output: AutomationOutputLoader):
        self.ground_truth = ground_truth
        self.output = output
        self.results = []

    def validate_fact_counts(self, domain_filter: Optional[str] = None) -> List[Dict]:
        """Validate fact counts by domain and entity"""
        results = []

        domains = [domain_filter] if domain_filter else self.ground_truth.get_all_domains()

        for domain in domains:
            expected_target = self.ground_truth.get_expected(domain, "target")
            expected_buyer = self.ground_truth.get_expected(domain, "buyer")
            expected_total = self.ground_truth.get_expected(domain)

            actual_target = self.output.facts.get(domain, {}).get("target", 0)
            actual_buyer = self.output.facts.get(domain, {}).get("buyer", 0)
            actual_total = self.output.facts.get(domain, {}).get("total", 0)

            # Calculate accuracy
            target_accuracy = self._calculate_accuracy(actual_target, expected_target)
            buyer_accuracy = self._calculate_accuracy(actual_buyer, expected_buyer)
            total_accuracy = self._calculate_accuracy(actual_total, expected_total)

            # Determine status
            status = self._determine_status(total_accuracy, expected_total, actual_total)

            results.append({
                "domain": domain,
                "category": "fact_counts",
                "expected": {
                    "target": expected_target,
                    "buyer": expected_buyer,
                    "total": expected_total
                },
                "actual": {
                    "target": actual_target,
                    "buyer": actual_buyer,
                    "total": actual_total
                },
                "accuracy": {
                    "target": target_accuracy,
                    "buyer": buyer_accuracy,
                    "total": total_accuracy
                },
                "status": status
            })

        self.results.extend(results)
        return results

    def validate_inventory_counts(self) -> List[Dict]:
        """Validate inventory item counts (exact match for applications)"""
        results = []

        # Applications should match exactly (38 target, 9 buyer)
        expected_apps_target = 38
        expected_apps_buyer = 9

        actual_apps_target = self.output.inventory.get("application", {}).get("target", 0)
        actual_apps_buyer = self.output.inventory.get("application", {}).get("buyer", 0)

        # Exact match for applications
        apps_match = (actual_apps_target == expected_apps_target and
                     actual_apps_buyer == expected_apps_buyer)

        results.append({
            "category": "inventory_counts",
            "item_type": "applications",
            "expected": {
                "target": expected_apps_target,
                "buyer": expected_apps_buyer,
                "total": expected_apps_target + expected_apps_buyer
            },
            "actual": {
                "target": actual_apps_target,
                "buyer": actual_apps_buyer,
                "total": actual_apps_target + actual_apps_buyer
            },
            "status": "PASS" if apps_match else "FAIL",
            "exact_match_required": True
        })

        self.results.extend(results)
        return results

    def validate_reasoning_outputs(self) -> Dict:
        """Validate reasoning phase outputs (risks, work items, etc.)"""
        result = {
            "category": "reasoning_outputs",
            "checks": []
        }

        # Expected: ≥10 risks, ≥12 work items
        risks_count = self.output.findings.get("risks", {}).get("count", 0)
        work_items_count = self.output.findings.get("work_items", {}).get("count", 0)
        total_findings = self.output.findings.get("total", 0)

        # Check 1: Findings exist
        result["checks"].append({
            "name": "Findings exist",
            "expected": "> 0",
            "actual": total_findings,
            "status": "PASS" if total_findings > 0 else "FAIL",
            "message": "Reasoning phase executed" if total_findings > 0 else "Reasoning phase NOT executed (0 findings)"
        })

        # Check 2: Risks threshold
        result["checks"].append({
            "name": "Risks count",
            "expected": "≥ 10",
            "actual": risks_count,
            "status": "PASS" if risks_count >= 10 else "WARNING" if risks_count > 0 else "FAIL",
            "message": f"Found {risks_count} risks"
        })

        # Check 3: Work items threshold
        result["checks"].append({
            "name": "Work items count",
            "expected": "≥ 12",
            "actual": work_items_count,
            "status": "PASS" if work_items_count >= 12 else "WARNING" if work_items_count > 0 else "FAIL",
            "message": f"Found {work_items_count} work items"
        })

        # Overall status
        statuses = [check["status"] for check in result["checks"]]
        if "FAIL" in statuses:
            result["status"] = "FAIL"
        elif "WARNING" in statuses:
            result["status"] = "WARNING"
        else:
            result["status"] = "PASS"

        self.results.append(result)
        return result

    def validate_entity_scoping(self) -> Dict:
        """Validate entity distribution (both target and buyer should be present)"""
        result = {
            "category": "entity_scoping",
            "checks": []
        }

        # Check if both entities are present across all domains
        total_target_facts = sum(
            domain_data.get("target", 0)
            for domain_data in self.output.facts.values()
        )
        total_buyer_facts = sum(
            domain_data.get("buyer", 0)
            for domain_data in self.output.facts.values()
        )

        # Check 1: Target facts exist
        result["checks"].append({
            "name": "Target facts present",
            "expected": "> 0",
            "actual": total_target_facts,
            "status": "PASS" if total_target_facts > 0 else "FAIL",
            "message": f"Found {total_target_facts} target facts"
        })

        # Check 2: Buyer facts exist
        result["checks"].append({
            "name": "Buyer facts present",
            "expected": "> 0",
            "actual": total_buyer_facts,
            "status": "PASS" if total_buyer_facts > 0 else "FAIL",
            "message": f"Found {total_buyer_facts} buyer facts" if total_buyer_facts > 0
                      else "Entity detection FAILURE - 0 buyer facts"
        })

        # Check 3: Distribution not 100% target / 0% buyer
        if total_target_facts > 0 and total_buyer_facts > 0:
            buyer_percentage = (total_buyer_facts / (total_target_facts + total_buyer_facts)) * 100
            result["checks"].append({
                "name": "Entity distribution",
                "expected": "Both entities present",
                "actual": f"{buyer_percentage:.1f}% buyer",
                "status": "PASS",
                "message": f"Healthy distribution: {total_target_facts} target, {total_buyer_facts} buyer"
            })

        # Overall status
        statuses = [check["status"] for check in result["checks"]]
        result["status"] = "FAIL" if "FAIL" in statuses else "PASS"

        self.results.append(result)
        return result

    def detect_known_failures(self) -> Dict:
        """Detect known failure modes from ground truth document"""
        result = {
            "category": "known_failure_modes",
            "failures_detected": []
        }

        # Known failure 1: Organization fact explosion (>400 facts instead of ~15)
        org_facts = self.output.facts.get("organization", {}).get("total", 0)
        if org_facts > 400:
            result["failures_detected"].append({
                "name": "Organization fact explosion",
                "description": f"Found {org_facts} organization facts (expected ~15)",
                "severity": "CRITICAL",
                "cause": "Extracting one fact per table row instead of aggregated facts"
            })

        # Known failure 2: Entity detection failure (0 buyer facts)
        total_buyer = sum(d.get("buyer", 0) for d in self.output.facts.values())
        if total_buyer == 0:
            total_target = sum(d.get("target", 0) for d in self.output.facts.values())
            if total_target > 0:
                result["failures_detected"].append({
                    "name": "Entity detection failure",
                    "description": "All facts tagged as 'target', 0 buyer facts found",
                    "severity": "CRITICAL",
                    "cause": "Entity detection logic defaulting all facts to 'target'"
                })

        # Known failure 3: Reasoning phase not executed (0 findings)
        if self.output.findings.get("total", 0) == 0:
            result["failures_detected"].append({
                "name": "Reasoning phase not executed",
                "description": "0 risks, 0 work items, 0 findings of any type",
                "severity": "CRITICAL",
                "cause": "Web app only runs Phase 1 (Discovery), Phase 2 (Reasoning) never called"
            })

        # Known failure 4: Inventory count inflation (apps >50)
        app_count = self.output.inventory.get("application", {}).get("total", 0)
        if app_count > 50:
            result["failures_detected"].append({
                "name": "Inventory count inflation",
                "description": f"Found {app_count} applications (expected 38 target + 9 buyer = 47)",
                "severity": "HIGH",
                "cause": "Counting facts instead of inventory items, or duplicate entries"
            })

        result["status"] = "FAIL" if result["failures_detected"] else "PASS"
        result["count"] = len(result["failures_detected"])

        self.results.append(result)
        return result

    def _calculate_accuracy(self, actual: int, expected: int) -> float:
        """Calculate percentage accuracy"""
        if expected == 0:
            return 100.0 if actual == 0 else 0.0
        return (actual / expected) * 100.0

    def _determine_status(self, accuracy: float, expected: int, actual: int) -> str:
        """Determine validation status based on accuracy and tolerance"""
        if expected == 0 and actual == 0:
            return "PASS"

        # ±10% tolerance
        if 90.0 <= accuracy <= 110.0:
            return "PASS"
        elif 80.0 <= accuracy <= 120.0:
            return "WARNING"
        else:
            return "FAIL"


class ReportGenerator:
    """Generates validation reports in various formats"""

    def __init__(self, validator: Validator):
        self.validator = validator
        self.results = validator.results

    def generate_terminal_report(self, verbose: bool = False) -> None:
        """Generate colored terminal output"""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}IT DUE DILIGENCE AUTOMATION VALIDATION REPORT{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Ground Truth: EXPECTED_FACTS_GROUND_TRUTH.md\n")

        # Overall summary
        statuses = [r.get("status") for r in self.results if "status" in r]
        pass_count = statuses.count("PASS")
        warning_count = statuses.count("WARNING")
        fail_count = statuses.count("FAIL")

        overall = "PASS" if fail_count == 0 else "FAIL"
        color = Colors.GREEN if overall == "PASS" else Colors.RED

        print(f"{Colors.BOLD}Overall Status: {color}{overall}{Colors.END}\n")
        print(f"  ✅ PASS: {pass_count}")
        print(f"  ⚠️  WARNING: {warning_count}")
        print(f"  ❌ FAIL: {fail_count}\n")

        # Known failure modes (if any)
        for result in self.results:
            if result.get("category") == "known_failure_modes":
                if result["failures_detected"]:
                    print(f"{Colors.RED}{Colors.BOLD}🚨 KNOWN FAILURE MODES DETECTED:{Colors.END}\n")
                    for failure in result["failures_detected"]:
                        print(f"  {Colors.RED}❌ {failure['name']}{Colors.END}")
                        print(f"     {failure['description']}")
                        print(f"     Cause: {failure['cause']}\n")

        # Fact counts by domain
        print(f"{Colors.BOLD}FACT COUNTS BY DOMAIN:{Colors.END}\n")
        print(f"{'Domain':<20} {'Expected':<12} {'Actual':<12} {'Accuracy':<12} {'Status':<10}")
        print("-" * 80)

        for result in self.results:
            if result.get("category") == "fact_counts":
                domain = result["domain"].upper()
                expected = result["expected"]["total"]
                actual = result["actual"]["total"]
                accuracy = result["accuracy"]["total"]
                status = result["status"]

                status_color = self._get_status_color(status)
                status_symbol = self._get_status_symbol(status)

                print(f"{domain:<20} {expected:<12} {actual:<12} {accuracy:>6.1f}%{'':<6} {status_color}{status_symbol} {status}{Colors.END}")

                if verbose:
                    print(f"  └─ Target: {result['actual']['target']} (expected {result['expected']['target']})")
                    print(f"  └─ Buyer:  {result['actual']['buyer']} (expected {result['expected']['buyer']})")

        # Inventory counts
        print(f"\n{Colors.BOLD}INVENTORY COUNTS:{Colors.END}\n")
        for result in self.results:
            if result.get("category") == "inventory_counts":
                status_color = self._get_status_color(result["status"])
                status_symbol = self._get_status_symbol(result["status"])

                print(f"Applications: {result['actual']['total']} (expected {result['expected']['total']})")
                print(f"  └─ Target: {result['actual']['target']} (expected {result['expected']['target']})")
                print(f"  └─ Buyer:  {result['actual']['buyer']} (expected {result['expected']['buyer']})")
                print(f"  Status: {status_color}{status_symbol} {result['status']}{Colors.END}\n")

        # Reasoning outputs
        print(f"{Colors.BOLD}REASONING OUTPUTS:{Colors.END}\n")
        for result in self.results:
            if result.get("category") == "reasoning_outputs":
                for check in result["checks"]:
                    status_color = self._get_status_color(check["status"])
                    status_symbol = self._get_status_symbol(check["status"])
                    print(f"{check['name']:<30} {status_color}{status_symbol} {check['status']}{Colors.END}  ({check['message']})")

        # Entity scoping
        print(f"\n{Colors.BOLD}ENTITY SCOPING:{Colors.END}\n")
        for result in self.results:
            if result.get("category") == "entity_scoping":
                for check in result["checks"]:
                    status_color = self._get_status_color(check["status"])
                    status_symbol = self._get_status_symbol(check["status"])
                    print(f"{check['name']:<30} {status_color}{status_symbol} {check['status']}{Colors.END}  ({check['message']})")

        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}\n")

    def generate_json_report(self, output_path: str) -> None:
        """Generate JSON report for machine consumption"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": self._get_overall_status(),
            "results": self.results
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"JSON report saved to: {output_path}")

    def generate_markdown_report(self, output_path: str) -> None:
        """Generate detailed markdown report"""
        lines = []
        lines.append("# IT Due Diligence Automation Validation Report\n")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**Overall Status:** {self._get_overall_status()}\n")
        lines.append("---\n")

        # Known failure modes
        for result in self.results:
            if result.get("category") == "known_failure_modes":
                if result["failures_detected"]:
                    lines.append("## 🚨 Known Failure Modes Detected\n")
                    for failure in result["failures_detected"]:
                        lines.append(f"### {failure['name']} ({failure['severity']})\n")
                        lines.append(f"**Description:** {failure['description']}\n")
                        lines.append(f"**Cause:** {failure['cause']}\n")

        # Fact counts
        lines.append("## Fact Counts by Domain\n")
        lines.append("| Domain | Expected | Actual | Accuracy | Status |\n")
        lines.append("|--------|----------|--------|----------|--------|\n")

        for result in self.results:
            if result.get("category") == "fact_counts":
                domain = result["domain"].upper()
                expected = result["expected"]["total"]
                actual = result["actual"]["total"]
                accuracy = result["accuracy"]["total"]
                status = result["status"]
                status_icon = "✅" if status == "PASS" else "⚠️" if status == "WARNING" else "❌"
                lines.append(f"| {domain} | {expected} | {actual} | {accuracy:.1f}% | {status_icon} {status} |\n")

        # Additional sections...
        lines.append("\n---\n")
        lines.append("*Report generated by validate_automation.py*\n")

        with open(output_path, 'w') as f:
            f.writelines(lines)

        print(f"Markdown report saved to: {output_path}")

    def _get_overall_status(self) -> str:
        """Calculate overall validation status"""
        statuses = [r.get("status") for r in self.results if "status" in r]
        if "FAIL" in statuses:
            return "FAIL"
        elif "WARNING" in statuses:
            return "WARNING"
        else:
            return "PASS"

    def _get_status_color(self, status: str) -> str:
        """Get terminal color for status"""
        if status == "PASS":
            return Colors.GREEN
        elif status == "WARNING":
            return Colors.YELLOW
        else:
            return Colors.RED

    def _get_status_symbol(self, status: str) -> str:
        """Get status symbol"""
        if status == "PASS":
            return "✅"
        elif status == "WARNING":
            return "⚠️"
        else:
            return "❌"


def main():
    parser = argparse.ArgumentParser(
        description="Validate IT due diligence automation output against expected facts ground truth",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate using facts JSON and database
  python validate_automation.py --facts output/facts/facts_20260213.json --db data/diligence.db --deal-id abc123

  # Validate specific domain only
  python validate_automation.py --facts output/facts/facts_20260213.json --domain organization

  # Generate JSON and markdown reports
  python validate_automation.py --facts output/facts/facts_20260213.json --db data/diligence.db --deal-id abc123 --json-output validation.json --md-output validation.md

  # Verbose output
  python validate_automation.py --facts output/facts/facts_20260213.json --verbose

Exit codes:
  0 = All validations pass
  1 = Critical failures detected
  2 = Warnings only (no hard failures)
        """
    )

    # Required arguments
    parser.add_argument(
        '--facts',
        required=True,
        help='Path to facts JSON file (e.g., output/facts/facts_TIMESTAMP.json)'
    )

    # Optional arguments
    parser.add_argument(
        '--db',
        default='data/diligence.db',
        help='Path to database (default: data/diligence.db)'
    )

    parser.add_argument(
        '--deal-id',
        help='Deal ID to query inventory and findings (required if using database)'
    )

    parser.add_argument(
        '--ground-truth',
        default='EXPECTED_FACTS_GROUND_TRUTH.md',
        help='Path to ground truth markdown file (default: EXPECTED_FACTS_GROUND_TRUTH.md)'
    )

    parser.add_argument(
        '--domain',
        choices=['organization', 'applications', 'infrastructure', 'network',
                'cybersecurity', 'identity_access', 'executive_profile'],
        help='Validate specific domain only'
    )

    parser.add_argument(
        '--json-output',
        help='Path to save JSON validation report'
    )

    parser.add_argument(
        '--md-output',
        help='Path to save Markdown validation report'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output with detailed breakdowns'
    )

    args = parser.parse_args()

    try:
        # Load ground truth
        print(f"Loading ground truth from: {args.ground_truth}")
        ground_truth = GroundTruthParser(args.ground_truth)
        print(f"✓ Ground truth loaded ({len(ground_truth.get_all_domains())} domains)\n")

        # Load automation output
        print(f"Loading automation output...")
        output = AutomationOutputLoader()

        # Load facts
        output.load_facts(args.facts)
        print(f"✓ Facts loaded ({sum(d.get('total', 0) for d in output.facts.values())} total facts)")

        # Load inventory (if database and deal_id provided)
        if args.deal_id and Path(args.db).exists():
            output.load_inventory(args.deal_id, args.db)
            total_inventory = sum(d.get('total', 0) for d in output.inventory.values())
            print(f"✓ Inventory loaded ({total_inventory} total items)")

            # Load findings
            output.load_findings(args.deal_id, args.db)
            print(f"✓ Findings loaded ({output.findings.get('total', 0)} total findings)")
        else:
            print("⚠ Skipping inventory and findings (no database or deal_id provided)")

        # Run validations
        print("\nRunning validations...\n")
        validator = Validator(ground_truth, output)

        validator.validate_fact_counts(args.domain)
        validator.validate_inventory_counts()
        validator.validate_reasoning_outputs()
        validator.validate_entity_scoping()
        validator.detect_known_failures()

        # Generate reports
        report_gen = ReportGenerator(validator)
        report_gen.generate_terminal_report(args.verbose)

        if args.json_output:
            report_gen.generate_json_report(args.json_output)

        if args.md_output:
            report_gen.generate_markdown_report(args.md_output)

        # Determine exit code
        overall_status = report_gen._get_overall_status()
        if overall_status == "FAIL":
            sys.exit(1)
        elif overall_status == "WARNING":
            sys.exit(2)
        else:
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
