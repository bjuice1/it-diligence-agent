"""
Fact Verification UI - Streamlit Components

Human-in-the-loop verification system to anchor LLM outputs
to human-verified facts, preventing hallucinations.

Components:
- Verification Dashboard: Stats overview
- Verification Queue: Unverified facts awaiting review
- Verification History: Audit trail of verifications
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from stores.fact_store import FactStore
except ImportError as e:
    st.error(f"Import error: {e}")


def render_verification_dashboard(fact_store: FactStore):
    """
    Render verification statistics dashboard.

    Shows:
    - Overall verification rate
    - Breakdown by domain
    - Verified vs unverified counts
    """
    st.subheader("Verification Dashboard")

    if not fact_store or len(fact_store.facts) == 0:
        st.info("No facts available. Run extraction first.")
        return

    stats = fact_store.get_verification_stats()

    # Main metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        rate = stats["verification_rate"]
        st.metric(
            "Verification Rate",
            f"{rate:.0%}",
            delta="Verified" if rate > 0.8 else "Needs Review"
        )

    with col2:
        st.metric("Total Facts", stats["total_facts"])

    with col3:
        st.metric("Verified", stats["verified_count"])

    with col4:
        st.metric("Unverified", stats["unverified_count"])

    st.divider()

    # Domain breakdown
    st.markdown("**Verification by Domain**")

    domain_data = []
    for domain, domain_stats in stats["by_domain"].items():
        domain_data.append({
            "Domain": domain.replace("_", " ").title(),
            "Total": domain_stats["total"],
            "Verified": domain_stats["verified"],
            "Rate": f"{domain_stats['rate']:.0%}",
            "Status": "✅" if domain_stats["rate"] >= 0.8 else "⚠️" if domain_stats["rate"] >= 0.5 else "❌"
        })

    if domain_data:
        df = pd.DataFrame(domain_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_verification_queue(fact_store: FactStore, session_dir: Path):
    """
    Render the verification queue - unverified facts awaiting review.

    Allows users to:
    - See evidence quote
    - Mark as verified
    - Filter by domain
    """
    st.subheader("Verification Queue")

    if not fact_store or len(fact_store.facts) == 0:
        st.info("No facts available.")
        return

    unverified = fact_store.get_unverified_facts()

    if not unverified:
        st.success("All facts have been verified!")
        return

    # Filter options
    col1, col2 = st.columns([2, 1])

    with col1:
        domains = list(set(f.domain for f in unverified))
        domain_options = ["All"] + sorted(domains)
        selected_domain = st.selectbox("Filter by Domain", domain_options, key="verify_domain_filter")

    with col2:
        # Verifier name input
        verifier = st.text_input("Your Name/Email", key="verifier_name", placeholder="reviewer@company.com")

    if selected_domain != "All":
        unverified = [f for f in unverified if f.domain == selected_domain]

    st.caption(f"Showing {len(unverified)} unverified facts")
    st.divider()

    # Display facts in verification cards
    for i, fact in enumerate(unverified[:20]):  # Limit to 20 at a time
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                st.markdown(f"**{fact.fact_id}** - {fact.item}")
                st.caption(f"Domain: {fact.domain} | Category: {fact.category}")

                # Show evidence quote
                quote = fact.evidence.get("exact_quote", "No quote available")
                with st.expander("View Evidence"):
                    st.markdown(f'> "{quote}"')
                    if fact.source_document:
                        st.caption(f"Source: {fact.source_document}")

                    # Show details if any
                    if fact.details:
                        st.markdown("**Details:**")
                        for k, v in fact.details.items():
                            st.markdown(f"- {k}: {v}")

            with col2:
                # Verify button
                if verifier:
                    if st.button("✅ Verify", key=f"verify_{fact.fact_id}"):
                        if fact_store.verify_fact(fact.fact_id, verifier):
                            # Save the updated store
                            facts_path = session_dir / "facts.json"
                            if facts_path.exists():
                                fact_store.save(str(facts_path))
                            st.success("Verified!")
                            st.rerun()
                else:
                    st.caption("Enter name to verify")

            st.markdown("---")

    if len(unverified) > 20:
        st.info(f"Showing first 20 of {len(unverified)} unverified facts. Verify some to see more.")


def render_verified_facts(fact_store: FactStore):
    """
    Render list of verified facts with audit trail.
    """
    st.subheader("Verified Facts")

    if not fact_store or len(fact_store.facts) == 0:
        st.info("No facts available.")
        return

    verified = fact_store.get_verified_facts()

    if not verified:
        st.info("No facts have been verified yet.")
        return

    # Build table data
    rows = []
    for fact in verified:
        rows.append({
            "ID": fact.fact_id,
            "Item": fact.item[:50] + "..." if len(fact.item) > 50 else fact.item,
            "Domain": fact.domain,
            "Verified By": fact.verified_by or "Unknown",
            "Verified At": fact.verified_at[:10] if fact.verified_at else "Unknown",
            "Status": "✅"
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_bulk_verification(fact_store: FactStore, session_dir: Path):
    """
    Bulk verification tools - verify multiple facts at once.
    """
    st.subheader("Bulk Verification")

    if not fact_store or len(fact_store.facts) == 0:
        st.info("No facts available.")
        return

    unverified = fact_store.get_unverified_facts()

    if not unverified:
        st.success("All facts have been verified!")
        return

    verifier = st.text_input("Verifier Name/Email", key="bulk_verifier", placeholder="reviewer@company.com")

    col1, col2 = st.columns(2)

    with col1:
        # Verify by domain
        st.markdown("**Verify All in Domain**")
        domains = list(set(f.domain for f in unverified))

        for domain in domains:
            domain_facts = [f for f in unverified if f.domain == domain]
            if st.button(f"Verify All {domain} ({len(domain_facts)})", key=f"bulk_{domain}"):
                if verifier:
                    fact_ids = [f.fact_id for f in domain_facts]
                    results = fact_store.bulk_verify(fact_ids, verifier)
                    # Save
                    facts_path = session_dir / "facts.json"
                    if facts_path.exists():
                        fact_store.save(str(facts_path))
                    st.success(f"Verified {results['verified']} facts!")
                    st.rerun()
                else:
                    st.warning("Enter verifier name first")

    with col2:
        # Verify all
        st.markdown("**Verify Everything**")
        st.warning(f"This will verify {len(unverified)} facts")
        if st.button("⚠️ Verify All Unverified", key="verify_all"):
            if verifier:
                fact_ids = [f.fact_id for f in unverified]
                results = fact_store.bulk_verify(fact_ids, verifier)
                # Save
                facts_path = session_dir / "facts.json"
                if facts_path.exists():
                    fact_store.save(str(facts_path))
                st.success(f"Verified {results['verified']} facts!")
                st.rerun()
            else:
                st.warning("Enter verifier name first")


def render_verification_section(session_dir: Path):
    """
    Main entry point for the verification UI.

    Creates tabs for Dashboard, Queue, Verified, and Bulk tools.
    """
    # Load fact store
    facts_path = session_dir / "facts.json"

    if not facts_path.exists():
        st.info("No facts file found. Run analysis first to generate facts.")
        return

    try:
        fact_store = FactStore.load(str(facts_path))
    except Exception as e:
        st.error(f"Error loading facts: {e}")
        return

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Dashboard",
        "Verification Queue",
        "Verified Facts",
        "Bulk Tools"
    ])

    with tab1:
        render_verification_dashboard(fact_store)

    with tab2:
        render_verification_queue(fact_store, session_dir)

    with tab3:
        render_verified_facts(fact_store)

    with tab4:
        render_bulk_verification(fact_store, session_dir)


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Fact Verification", layout="wide")
    st.title("Fact Verification")

    session_dir = st.text_input(
        "Session Directory",
        value="sessions/test_session"
    )

    if session_dir:
        render_verification_section(Path(session_dir))
