"""
Interactive CLI for IT Due Diligence Agent.

Provides a polished REPL (Read-Eval-Print Loop) for reviewing and adjusting analysis outputs.
Designed for usability with contextual help, shortcuts, and visual feedback.
"""

import shlex
import sys
from pathlib import Path
from typing import Optional, List, Dict

from .session import Session
from .commands import COMMANDS


# Command aliases for quick access
ALIASES = {
    # Navigation shortcuts
    '?': 'help',
    'h': 'help',
    's': 'status',
    'd': 'dashboard',
    'q': 'exit',

    # List shortcuts
    'lf': ['list', 'facts'],
    'lr': ['list', 'risks'],
    'lw': ['list', 'work-items'],
    'lg': ['list', 'gaps'],
    'la': ['list', 'all'],

    # Common actions
    'e': 'explain',
    'a': 'adjust',
    'u': 'undo',
    'x': 'export',
    'n': 'note',
    'del': 'delete',
    'find': 'search',
    'hist': 'history',
}


class InteractiveCLI:
    """
    Interactive command-line interface for the IT DD Agent.

    Provides a polished shell experience for:
    - Reviewing facts, risks, work items
    - Adjusting findings (severity, phase, cost, owner)
    - Adding deal context
    - Exporting modified results
    """

    def __init__(self, session: Session):
        self.session = session
        self.running = False
        self.last_command = None
        self.command_history: List[str] = []

    @classmethod
    def from_files(
        cls,
        facts_file: Optional[Path] = None,
        findings_file: Optional[Path] = None,
        deal_context_file: Optional[Path] = None
    ) -> 'InteractiveCLI':
        """Create CLI from existing output files."""
        session = Session.load_from_files(
            facts_file=facts_file,
            findings_file=findings_file,
            deal_context_file=deal_context_file
        )
        return cls(session)

    @classmethod
    def from_session(cls, session: Session) -> 'InteractiveCLI':
        """Create CLI from existing session."""
        return cls(session)

    def parse_command(self, input_str: str) -> tuple:
        """
        Parse user input into command and args.
        Handles aliases and shortcuts.
        """
        input_str = input_str.strip()
        if not input_str:
            return (None, [])

        try:
            parts = shlex.split(input_str)
        except ValueError as e:
            return ('_error', [str(e)])

        if not parts:
            return (None, [])

        command = parts[0].lower()
        args = parts[1:]

        # Handle aliases
        if command in ALIASES:
            alias_value = ALIASES[command]
            if isinstance(alias_value, list):
                # Alias expands to command + args
                command = alias_value[0]
                args = alias_value[1:] + args
            else:
                command = alias_value

        return (command, args)

    def execute_command(self, command: str, args: list) -> str:
        """Execute a single command and return output."""
        if command is None:
            return ""

        if command == '_error':
            return f"Parse error: {args[0]}\nTip: Make sure quotes are properly closed."

        if command in ['exit', 'quit']:
            return self._handle_exit()

        if command == 'dashboard':
            return self._show_dashboard()

        if command in COMMANDS:
            try:
                self.last_command = command
                return COMMANDS[command](self.session, args)
            except Exception as e:
                return self._format_error(command, str(e))

        # Unknown command - provide helpful suggestions
        return self._suggest_command(command)

    def _format_error(self, command: str, error: str) -> str:
        """Format error message with helpful context."""
        output = [f"\nError: {error}"]

        # Add command-specific help
        if command == 'adjust':
            output.append("\nTip: adjust <id> <field> <value>")
            output.append("  Example: adjust R-001 severity critical")
        elif command == 'explain':
            output.append("\nTip: explain <id>")
            output.append("  Example: explain R-001")
        elif command == 'add':
            output.append("\nTip: Try 'help add' to see all options")

        return "\n".join(output)

    def _suggest_command(self, unknown: str) -> str:
        """Suggest similar commands for unknown input."""
        all_commands = list(COMMANDS.keys()) + ['exit', 'quit', 'dashboard']

        # Find similar commands
        suggestions = []
        for cmd in all_commands:
            if unknown in cmd or cmd.startswith(unknown[:2]):
                suggestions.append(cmd)

        output = [f"Unknown command: '{unknown}'"]

        if suggestions:
            output.append(f"Did you mean: {', '.join(suggestions[:3])}?")

        output.append("\nQuick shortcuts:")
        output.append("  d = dashboard    s = status    ? = help")
        output.append("  lr = list risks  lw = list work-items")

        return "\n".join(output)

    def _handle_exit(self) -> str:
        """Handle exit command with unsaved changes check."""
        if self.session.has_unsaved_changes:
            count = self.session.unsaved_change_count
            return f"_EXIT_CHECK:{count}"

        self.running = False
        return "_EXIT"

    def confirm_exit(self) -> bool:
        """Prompt user to confirm exit with unsaved changes."""
        count = self.session.unsaved_change_count
        print(f"\n{'='*50}")
        print(f"  You have {count} unsaved change(s)")
        print(f"{'='*50}")
        print("\n  [s] Save changes and exit")
        print("  [d] Discard changes and exit")
        print("  [c] Cancel - stay in session")

        try:
            choice = input("\n  Your choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = 'c'

        if choice == 's':
            output = COMMANDS['export'](self.session, [])
            print(output)
            return True
        elif choice == 'd':
            print("\n  Changes discarded.")
            return True
        else:
            print("\n  Continuing session...")
            return False

    def _show_dashboard(self) -> str:
        """Show a visual dashboard of the analysis."""
        summary = self.session.get_summary()
        risk_sum = summary['risk_summary']
        cost_sum = summary['cost_summary']

        # Calculate total cost
        total_low = sum(p['low'] for p in cost_sum.values())
        total_high = sum(p['high'] for p in cost_sum.values())

        output = []
        output.append("")
        output.append("=" * 60)
        output.append("                    ANALYSIS DASHBOARD")
        output.append("=" * 60)

        # Coverage section
        output.append("")
        output.append("  COVERAGE")
        output.append("  " + "-" * 40)
        domains = summary['domains_with_facts']
        if domains:
            output.append(f"  Domains analyzed: {', '.join(domains)}")
        output.append(f"  Facts extracted:  {summary['facts']}")
        output.append(f"  Gaps identified:  {summary['gaps']}")

        # Risk section with visual indicators
        output.append("")
        output.append("  RISKS")
        output.append("  " + "-" * 40)
        total_risks = summary['risks']
        if total_risks > 0:
            # Visual bar for risk distribution
            crit = risk_sum['critical']
            high = risk_sum['high']
            med = risk_sum['medium']
            low = risk_sum['low']

            output.append(f"  Critical: {crit:>3}  {'*' * crit}")
            output.append(f"  High:     {high:>3}  {'*' * high}")
            output.append(f"  Medium:   {med:>3}  {'*' * med}")
            output.append(f"  Low:      {low:>3}  {'*' * low}")
            output.append(f"  " + "-" * 20)
            output.append(f"  Total:    {total_risks:>3}")
        else:
            output.append("  No risks identified yet")

        # Work items & cost section
        output.append("")
        output.append("  INTEGRATION WORK")
        output.append("  " + "-" * 40)
        if summary['work_items'] > 0:
            output.append(f"  Work items: {summary['work_items']}")
            output.append("")
            output.append("  Cost by Phase:")
            for phase in ['Day_1', 'Day_100', 'Post_100']:
                if cost_sum[phase]['count'] > 0:
                    low = cost_sum[phase]['low']
                    high = cost_sum[phase]['high']
                    cnt = cost_sum[phase]['count']
                    output.append(f"    {phase:>8}: ${low:>10,} - ${high:>10,}  ({cnt} items)")

            output.append("  " + "-" * 45)
            output.append(f"    {'Total':>8}: ${total_low:>10,} - ${total_high:>10,}")
        else:
            output.append("  No work items identified yet")

        # Session state
        output.append("")
        output.append("  SESSION")
        output.append("  " + "-" * 40)
        if summary['has_deal_context']:
            output.append("  Deal context: Set")
        else:
            output.append("  Deal context: Not set")

        if summary['modifications'] > 0:
            output.append(f"  Modifications: {summary['modifications']}")
            if summary['unsaved_changes'] > 0:
                output.append(f"  ** {summary['unsaved_changes']} unsaved changes **")

        # Quick actions
        output.append("")
        output.append("=" * 60)
        output.append("  QUICK ACTIONS")
        output.append("=" * 60)
        output.append("")

        # Contextual suggestions based on state
        if total_risks > 0:
            output.append("  lr              List all risks")
            output.append("  explain R-001   View risk details")
        if summary['work_items'] > 0:
            output.append("  lw              List work items")
        if summary['gaps'] > 0:
            output.append("  lg              List documentation gaps")
        if not summary['has_deal_context']:
            output.append("  add context \"...\"  Add deal context")
        if summary['unsaved_changes'] > 0:
            output.append("  export          Save your changes")

        output.append("")
        output.append("  Type 'help' for all commands, '?' for quick help")
        output.append("")

        return "\n".join(output)

    def _get_contextual_tip(self) -> str:
        """Get a contextual tip based on session state."""
        summary = self.session.get_summary()

        if summary['risks'] > 0 and not self.last_command:
            return "Tip: Type 'lr' to list risks, or 'd' for dashboard"

        if summary['unsaved_changes'] > 0:
            return f"Tip: You have {summary['unsaved_changes']} unsaved changes. Type 'x' to export."

        if not summary['has_deal_context']:
            return "Tip: Add deal context with: add context \"Healthcare deal - HIPAA applies\""

        return ""

    def print_banner(self):
        """Print welcome banner with dashboard."""
        summary = self.session.get_summary()

        print("")
        print("=" * 60)
        print("       IT Due Diligence Agent - Interactive Review")
        print("=" * 60)
        print("")
        print("  Welcome! This tool lets you review and refine the")
        print("  IT due diligence analysis before finalizing.")
        print("")
        print("  " + "-" * 50)
        print(f"  Loaded: {summary['facts']} facts | {summary['risks']} risks | {summary['work_items']} work items")

        if summary['domains_with_facts']:
            print(f"  Domains: {', '.join(summary['domains_with_facts'])}")

        # Show risk severity summary if we have risks
        if summary['risks'] > 0:
            rs = summary['risk_summary']
            risk_parts = []
            if rs['critical']: risk_parts.append(f"{rs['critical']} critical")
            if rs['high']: risk_parts.append(f"{rs['high']} high")
            if rs['medium']: risk_parts.append(f"{rs['medium']} medium")
            if rs['low']: risk_parts.append(f"{rs['low']} low")
            print(f"  Risk breakdown: {', '.join(risk_parts)}")

        print("  " + "-" * 50)
        print("")
        print("  GET STARTED:")
        print("    d         Show full dashboard")
        print("    lr        List all risks")
        print("    lw        List work items")
        print("    ?         Quick help")
        print("")

    def run(self):
        """
        Run the interactive REPL loop.

        This is the main entry point for interactive mode.
        """
        self.running = True
        self.print_banner()

        while self.running:
            try:
                # Build prompt
                prompt = "dd> "
                if self.session.has_unsaved_changes:
                    prompt = f"dd [{self.session.unsaved_change_count}*]> "

                user_input = input(prompt)
                self.command_history.append(user_input)

                # Parse and execute
                command, args = self.parse_command(user_input)
                output = self.execute_command(command, args)

                # Handle special outputs
                if output == "_EXIT":
                    break
                elif output.startswith("_EXIT_CHECK:"):
                    if self.confirm_exit():
                        break
                elif output:
                    print(output)

                    # Show contextual tip occasionally
                    if len(self.command_history) == 1:
                        tip = self._get_contextual_tip()
                        if tip:
                            print(f"\n  {tip}")

            except KeyboardInterrupt:
                print("\n\n  Interrupted. Type 'exit' or 'q' to quit.")
                continue
            except EOFError:
                print()
                if self.session.has_unsaved_changes:
                    if self.confirm_exit():
                        break
                else:
                    break

        print("\n  Session ended. Goodbye!")
        print("")


def run_interactive_mode(
    facts_file: Optional[Path] = None,
    findings_file: Optional[Path] = None,
    deal_context_file: Optional[Path] = None,
    session: Optional[Session] = None
):
    """
    Convenience function to start interactive mode.

    Can be called with either file paths or an existing session.
    """
    if session:
        cli = InteractiveCLI.from_session(session)
    else:
        cli = InteractiveCLI.from_files(
            facts_file=facts_file,
            findings_file=findings_file,
            deal_context_file=deal_context_file
        )

    cli.run()
