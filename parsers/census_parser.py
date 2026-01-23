"""
Census Data Parser

Parses HR census data from Excel/CSV files into StaffMember objects.
Handles:
- Auto-detection of column mappings
- Role classification into categories
- Tenure calculation from hire dates
- Compensation normalization
- Key person flagging based on tenure/role
"""

import csv
import logging
import re
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from models.organization_models import (
    StaffMember,
    RoleSummary,
    CategorySummary,
    RoleCategory,
    EmploymentType
)

logger = logging.getLogger(__name__)


# Column name mappings - common variations for each field
COLUMN_MAPPINGS = {
    "name": [
        "name", "employee_name", "full_name", "employee", "emp_name",
        "worker", "person", "staff_name", "associate"
    ],
    "first_name": [
        "first_name", "firstname", "first", "fname", "given_name"
    ],
    "last_name": [
        "last_name", "lastname", "last", "lname", "surname", "family_name"
    ],
    "role": [
        "title", "job_title", "role", "position", "job", "job_role",
        "position_title", "role_title", "designation"
    ],
    "department": [
        "department", "dept", "team", "group", "division", "org_unit",
        "business_unit", "cost_center", "function"
    ],
    "salary": [
        "salary", "base_salary", "compensation", "base_pay", "annual_salary",
        "base", "base_comp", "annual_pay", "pay_rate"
    ],
    "total_comp": [
        "total_comp", "total_compensation", "tc", "ote", "total_pay",
        "total_cash", "ttc", "total_target_comp"
    ],
    "location": [
        "location", "office", "site", "work_location", "city", "office_location",
        "work_site", "branch"
    ],
    "hire_date": [
        "hire_date", "start_date", "date_hired", "employment_date", "join_date",
        "hire_dt", "start_dt", "doh", "date_of_hire"
    ],
    "manager": [
        "manager", "reports_to", "supervisor", "manager_name", "reporting_to",
        "direct_manager", "mgr", "sup"
    ],
    "employment_type": [
        "employment_type", "emp_type", "worker_type", "employee_type", "status",
        "employment_status", "type", "classification"
    ],
    "employee_id": [
        "employee_id", "emp_id", "id", "worker_id", "badge", "employee_number",
        "emp_no", "personnel_number"
    ]
}

# Role classification rules - keywords that indicate category
ROLE_CLASSIFICATION_RULES = {
    RoleCategory.LEADERSHIP: [
        "cio", "ciso", "cto", "chief", "vp ", "vice president", "director",
        "head of", "manager", "lead", "principal", "executive"
    ],
    RoleCategory.INFRASTRUCTURE: [
        "network", "systems", "infrastructure", "server", "cloud", "devops",
        "sre", "platform", "storage", "virtualization", "vmware", "unix",
        "linux", "windows admin", "datacenter", "data center"
    ],
    RoleCategory.APPLICATIONS: [
        "developer", "programmer", "software", "application", "erp", "crm",
        "sap", "oracle apps", "salesforce", "web dev", "full stack", "backend",
        "frontend", "qa ", "quality", "test", "analyst"
    ],
    RoleCategory.SECURITY: [
        "security", "cyber", "infosec", "information security", "compliance",
        "risk", "audit", "soc ", "penetration", "vulnerability", "iam ",
        "identity", "grc"
    ],
    RoleCategory.SERVICE_DESK: [
        "help desk", "helpdesk", "service desk", "support", "desktop",
        "technician", "it support", "end user", "deskside"
    ],
    RoleCategory.DATA: [
        "dba", "database", "data engineer", "data analyst", "bi ", "business intelligence",
        "analytics", "etl", "data scientist", "data arch"
    ],
    RoleCategory.PROJECT_MANAGEMENT: [
        "project manager", "program manager", "pmo", "scrum", "agile",
        "delivery manager", "release manager"
    ]
}

# Tenure thresholds for key person consideration
KEY_PERSON_TENURE_YEARS = 5
KEY_PERSON_ROLES = ["cio", "ciso", "cto", "director", "manager", "architect", "lead", "principal"]


class CensusParser:
    """
    Parses HR census data from Excel or CSV files.

    Usage:
        parser = CensusParser()
        staff = parser.parse_file("census.xlsx", entity="target")
        summaries = parser.aggregate_by_category(staff)
    """

    def __init__(self):
        self.column_mappings = COLUMN_MAPPINGS.copy()
        self.role_rules = ROLE_CLASSIFICATION_RULES.copy()
        self._detected_columns: Dict[str, str] = {}
        self._parse_warnings: List[str] = []

    def parse_file(
        self,
        file_path: str,
        entity: str = "target",
        sheet_name: Optional[str] = None
    ) -> List[StaffMember]:
        """
        Parse a census file (Excel or CSV) into StaffMember objects.

        Args:
            file_path: Path to the census file
            entity: Entity identifier ("target", "buyer", "parent")
            sheet_name: For Excel files, which sheet to read (default: first)

        Returns:
            List of StaffMember objects
        """
        path = Path(file_path)
        self._parse_warnings = []

        if not path.exists():
            raise FileNotFoundError(f"Census file not found: {file_path}")

        # Determine file type and load data
        suffix = path.suffix.lower()
        if suffix in ['.xlsx', '.xls']:
            rows = self._load_excel(path, sheet_name)
        elif suffix == '.csv':
            rows = self._load_csv(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Use .xlsx, .xls, or .csv")

        if not rows:
            logger.warning(f"No data rows found in {file_path}")
            return []

        # First row is headers
        headers = rows[0]
        data_rows = rows[1:]

        # Detect column mappings
        self._detected_columns = self._detect_columns(headers)
        logger.info(f"Detected columns: {self._detected_columns}")

        # Parse each row
        staff_members = []
        for i, row in enumerate(data_rows, start=2):  # Start at 2 for Excel row numbers
            try:
                member = self._parse_row(row, headers, entity, i)
                if member:
                    staff_members.append(member)
            except Exception as e:
                self._parse_warnings.append(f"Row {i}: {str(e)}")
                logger.warning(f"Failed to parse row {i}: {e}")

        logger.info(f"Parsed {len(staff_members)} staff members from {file_path}")
        if self._parse_warnings:
            logger.warning(f"{len(self._parse_warnings)} warnings during parsing")

        return staff_members

    def _load_excel(self, path: Path, sheet_name: Optional[str]) -> List[List[Any]]:
        """Load data from Excel file."""
        try:
            import openpyxl
        except ImportError:
            # Fall back to csv if openpyxl not available
            logger.warning("openpyxl not installed, attempting pandas")
            try:
                import pandas as pd
                df = pd.read_excel(path, sheet_name=sheet_name or 0)
                rows = [df.columns.tolist()] + df.values.tolist()
                return rows
            except ImportError:
                raise ImportError("Install openpyxl or pandas to read Excel files: pip install openpyxl")

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

        if sheet_name:
            ws = wb[sheet_name]
        else:
            ws = wb.active

        rows = []
        for row in ws.iter_rows(values_only=True):
            # Skip completely empty rows
            if any(cell is not None for cell in row):
                rows.append(list(row))

        wb.close()
        return rows

    def _load_csv(self, path: Path) -> List[List[Any]]:
        """Load data from CSV file."""
        rows = []

        # Try to detect encoding
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding, newline='') as f:
                    reader = csv.reader(f)
                    rows = [row for row in reader if any(cell.strip() for cell in row)]
                break
            except UnicodeDecodeError:
                continue

        if not rows:
            raise ValueError(f"Could not decode CSV file with any standard encoding")

        return rows

    def _detect_columns(self, headers: List[str]) -> Dict[str, str]:
        """
        Auto-detect which columns map to which fields.

        Args:
            headers: List of column header names

        Returns:
            Dict mapping field names to actual column names
        """
        detected = {}
        headers_lower = [str(h).lower().strip() if h else "" for h in headers]

        for field, variations in self.column_mappings.items():
            for var in variations:
                var_lower = var.lower()
                for i, header in enumerate(headers_lower):
                    if var_lower == header or var_lower in header:
                        detected[field] = headers[i]
                        break
                if field in detected:
                    break

        return detected

    def _parse_row(
        self,
        row: List[Any],
        headers: List[str],
        entity: str,
        row_num: int
    ) -> Optional[StaffMember]:
        """Parse a single row into a StaffMember."""

        def get_value(field: str) -> Optional[str]:
            """Get value for a field from the row."""
            if field not in self._detected_columns:
                return None
            col_name = self._detected_columns[field]
            try:
                idx = headers.index(col_name)
                val = row[idx] if idx < len(row) else None
                return str(val).strip() if val is not None else None
            except (ValueError, IndexError):
                return None

        # Get name (required)
        name = get_value("name")
        if not name:
            # Try combining first + last name
            first = get_value("first_name") or ""
            last = get_value("last_name") or ""
            name = f"{first} {last}".strip()

        if not name:
            return None  # Skip rows without names

        # Get role (required)
        role_title = get_value("role")
        if not role_title:
            self._parse_warnings.append(f"Row {row_num}: No role title for {name}")
            role_title = "Unknown"

        # Get compensation
        salary_str = get_value("salary")
        base_compensation = self._parse_compensation(salary_str) if salary_str else 0

        total_comp_str = get_value("total_comp")
        total_compensation = self._parse_compensation(total_comp_str) if total_comp_str else None

        # Get other fields
        department = get_value("department") or "IT"
        location = get_value("location") or "Unknown"
        manager = get_value("manager")
        emp_type_str = get_value("employment_type")
        hire_date_str = get_value("hire_date")
        emp_id = get_value("employee_id")

        # Parse employment type
        if emp_type_str:
            employment_type = EmploymentType.from_string(emp_type_str)
        else:
            employment_type = EmploymentType.FTE

        # Parse hire date and calculate tenure
        tenure_years = None
        hire_date = None
        if hire_date_str:
            hire_date = self._parse_date(hire_date_str)
            if hire_date:
                tenure_years = self._calculate_tenure(hire_date)

        # Classify role
        role_category = self._classify_role(role_title, department)

        # Determine if key person
        is_key_person, key_person_reason = self._assess_key_person(
            role_title, role_category, tenure_years
        )

        # Generate ID
        if emp_id:
            member_id = f"{entity.upper()}-{emp_id}"
        else:
            member_id = f"{entity.upper()}-{uuid.uuid4().hex[:8].upper()}"

        return StaffMember(
            id=member_id,
            name=name,
            role_title=role_title,
            role_category=role_category,
            department=department,
            employment_type=employment_type,
            base_compensation=base_compensation,
            total_compensation=total_compensation,
            location=location,
            tenure_years=tenure_years,
            hire_date=hire_date,
            reports_to=manager,
            entity=entity,
            is_key_person=is_key_person,
            key_person_reason=key_person_reason
        )

    def _parse_compensation(self, value: str) -> float:
        """Parse compensation value, handling various formats."""
        if not value:
            return 0.0

        # Convert to string and clean
        value = str(value).strip()

        # Remove currency symbols and commas
        value = re.sub(r'[$£€,]', '', value)

        # Handle parentheses for negative (rare in salary but handle it)
        if value.startswith('(') and value.endswith(')'):
            value = '-' + value[1:-1]

        # Handle K notation (e.g., "85K" or "85k")
        k_match = re.match(r'^([\d.]+)\s*[kK]$', value)
        if k_match:
            return float(k_match.group(1)) * 1000

        try:
            return float(value)
        except ValueError:
            return 0.0

    def _parse_date(self, value: str) -> Optional[str]:
        """Parse date value into ISO format string."""
        if not value:
            return None

        # If it's already a date object
        if isinstance(value, (datetime, date)):
            return value.strftime("%Y-%m-%d")

        value = str(value).strip()

        # Common date formats to try
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m/%d/%y",
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Try pandas if available for more flexible parsing
        try:
            import pandas as pd
            dt = pd.to_datetime(value)
            return dt.strftime("%Y-%m-%d")
        except:
            pass

        logger.warning(f"Could not parse date: {value}")
        return None

    def _calculate_tenure(self, hire_date: str) -> float:
        """Calculate tenure in years from hire date."""
        try:
            hire = datetime.strptime(hire_date, "%Y-%m-%d")
            today = datetime.now()
            delta = today - hire
            return round(delta.days / 365.25, 1)
        except:
            return None

    def _classify_role(self, role_title: str, department: str) -> RoleCategory:
        """
        Classify a role into a category based on title and department.
        """
        title_lower = role_title.lower()
        dept_lower = department.lower() if department else ""

        # Check each category's keywords
        for category, keywords in self.role_rules.items():
            for keyword in keywords:
                if keyword in title_lower:
                    # Special handling: "manager" alone could be any category
                    # Only classify as leadership if it's a senior role
                    if keyword == "manager" and category == RoleCategory.LEADERSHIP:
                        # Check if it's a team manager vs IT manager
                        if any(x in title_lower for x in ["it manager", "director", "head", "vp"]):
                            return category
                        # Otherwise, check department
                        continue
                    return category

        # Fall back to department-based classification
        if "security" in dept_lower or "cyber" in dept_lower:
            return RoleCategory.SECURITY
        elif "infrastructure" in dept_lower or "network" in dept_lower:
            return RoleCategory.INFRASTRUCTURE
        elif "application" in dept_lower or "development" in dept_lower:
            return RoleCategory.APPLICATIONS
        elif "support" in dept_lower or "help" in dept_lower or "service" in dept_lower:
            return RoleCategory.SERVICE_DESK
        elif "data" in dept_lower or "analytics" in dept_lower:
            return RoleCategory.DATA

        return RoleCategory.OTHER

    def _assess_key_person(
        self,
        role_title: str,
        category: RoleCategory,
        tenure_years: Optional[float]
    ) -> Tuple[bool, Optional[str]]:
        """
        Assess if a person should be flagged as a key person risk.
        """
        reasons = []
        title_lower = role_title.lower()

        # Check for key roles
        is_key_role = any(kw in title_lower for kw in KEY_PERSON_ROLES)
        if is_key_role:
            reasons.append(f"Key role: {role_title}")

        # Check for leadership
        if category == RoleCategory.LEADERSHIP:
            reasons.append("Leadership position")

        # Check for long tenure
        if tenure_years and tenure_years >= KEY_PERSON_TENURE_YEARS:
            reasons.append(f"Long tenure ({tenure_years} years)")

        # Key person if any reason found
        if reasons:
            return True, "; ".join(reasons)

        return False, None

    def aggregate_by_category(
        self,
        staff: List[StaffMember],
        entity: str = "target"
    ) -> Dict[str, CategorySummary]:
        """
        Aggregate staff members by category.

        Args:
            staff: List of StaffMember objects
            entity: Filter to specific entity

        Returns:
            Dict mapping category name to CategorySummary
        """
        # Filter by entity
        filtered = [s for s in staff if s.entity == entity]

        # Group by category
        by_category: Dict[RoleCategory, List[StaffMember]] = {}
        for s in filtered:
            if s.role_category not in by_category:
                by_category[s.role_category] = []
            by_category[s.role_category].append(s)

        # Build summaries
        summaries = {}
        for category, members in by_category.items():
            # Aggregate roles within category
            roles = self.aggregate_by_role(members)

            # Calculate category totals
            total_headcount = len(members)
            total_comp = sum(m.total_compensation or 0 for m in members)
            avg_comp = total_comp / total_headcount if total_headcount > 0 else 0

            fte_count = sum(1 for m in members if m.employment_type == EmploymentType.FTE)
            contractor_count = sum(1 for m in members if m.employment_type == EmploymentType.CONTRACTOR)
            msp_count = sum(1 for m in members if m.employment_type == EmploymentType.MSP)

            summaries[category.value] = CategorySummary(
                category=category,
                total_headcount=total_headcount,
                total_compensation=total_comp,
                avg_compensation=avg_comp,
                roles=list(roles.values()),
                fte_count=fte_count,
                contractor_count=contractor_count,
                msp_count=msp_count
            )

        return summaries

    def aggregate_by_role(
        self,
        staff: List[StaffMember]
    ) -> Dict[str, RoleSummary]:
        """
        Aggregate staff members by role title.

        Args:
            staff: List of StaffMember objects

        Returns:
            Dict mapping role title to RoleSummary
        """
        by_role: Dict[str, List[StaffMember]] = {}

        for s in staff:
            # Normalize role title for grouping
            normalized = s.role_title.strip()
            if normalized not in by_role:
                by_role[normalized] = []
            by_role[normalized].append(s)

        summaries = {}
        for role_title, members in by_role.items():
            compensations = [m.total_compensation or m.base_compensation for m in members if m.base_compensation > 0]
            tenures = [m.tenure_years for m in members if m.tenure_years is not None]

            summaries[role_title] = RoleSummary(
                role_title=role_title,
                role_category=members[0].role_category,
                headcount=len(members),
                total_compensation=sum(compensations),
                avg_compensation=sum(compensations) / len(compensations) if compensations else 0,
                avg_tenure=sum(tenures) / len(tenures) if tenures else None,
                min_compensation=min(compensations) if compensations else 0,
                max_compensation=max(compensations) if compensations else 0,
                members=members
            )

        return summaries

    def get_parse_warnings(self) -> List[str]:
        """Get warnings from the most recent parse operation."""
        return self._parse_warnings.copy()

    def get_detected_columns(self) -> Dict[str, str]:
        """Get the column mappings detected in the most recent parse."""
        return self._detected_columns.copy()
