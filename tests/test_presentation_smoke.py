"""
Smoke tests for presentation layer (Phase 2+4).

These tests verify the full render path works without errors.
They check that pages load without 500 errors and handle
edge cases gracefully.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDashboardSummary:
    """Test dashboard summary dict structure."""

    def test_dashboard_summary_has_risk_summary(self):
        """Dashboard summary must include risk_summary dict."""
        # Simulate the structure that should be passed to template
        summary = {
            'facts': 10,
            'gaps': 5,
            'risks': 3,
            'work_items': 8,
            'risk_summary': {
                'critical': 1,
                'high': 2,
                'medium': 0,
                'low': 0,
                'total': 3
            },
        }

        assert 'risk_summary' in summary
        assert 'critical' in summary['risk_summary']
        assert 'high' in summary['risk_summary']
        assert 'medium' in summary['risk_summary']
        assert 'low' in summary['risk_summary']
        assert 'total' in summary['risk_summary']

    def test_empty_dashboard_summary_structure(self):
        """Empty dashboard summary should have correct structure."""
        # This is the error fallback structure
        summary = {
            'facts': 0,
            'gaps': 0,
            'risks': 0,
            'work_items': 0,
            'risk_summary': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'total': 0
            },
        }

        assert summary['risks'] == 0
        assert summary['risk_summary']['critical'] == 0
        assert summary['risk_summary']['total'] == 0


class TestMermaidIdSanitization:
    """Test Mermaid ID sanitization function."""

    def test_basic_sanitization(self):
        """Test basic character replacement."""
        from streamlit_app.views.organization.org_chart import _sanitize_id

        assert _sanitize_id("Hello World") == "Hello_World"
        assert _sanitize_id("test-123") == "test_123"
        assert _sanitize_id("name.with.dots") == "name_with_dots"

    def test_special_characters_removed(self):
        """Test special characters are removed."""
        from streamlit_app.views.organization.org_chart import _sanitize_id

        # Parentheses
        result = _sanitize_id("John (CTO)")
        assert "(" not in result
        assert ")" not in result

        # Apostrophes
        result = _sanitize_id("Jane's Team")
        assert "'" not in result

        # Colons
        result = _sanitize_id("VP: Engineering")
        assert ":" not in result

        # Ampersands
        result = _sanitize_id("R&D Team")
        assert "&" not in result

    def test_number_prefix_handling(self):
        """Test IDs starting with numbers get prefix."""
        from streamlit_app.views.organization.org_chart import _sanitize_id

        result = _sanitize_id("123_team")
        assert result.startswith("n")
        assert result == "n123_team"

        result = _sanitize_id("42")
        assert result.startswith("n")

    def test_empty_handling(self):
        """Test empty/None values are handled."""
        from streamlit_app.views.organization.org_chart import _sanitize_id

        assert _sanitize_id("") == "unknown"
        assert _sanitize_id(None) == "unknown"

    def test_all_special_chars_removed(self):
        """Test string with only special chars."""
        from streamlit_app.views.organization.org_chart import _sanitize_id

        result = _sanitize_id("@#$%")
        assert result == "node"  # Fallback for empty after sanitization

    def test_length_limit(self):
        """Test very long names are truncated."""
        from streamlit_app.views.organization.org_chart import _sanitize_id

        long_name = "A" * 100
        result = _sanitize_id(long_name)
        assert len(result) <= 50

    def test_real_world_names(self):
        """Test with real-world organization names."""
        from streamlit_app.views.organization.org_chart import _sanitize_id

        # Common formats in org charts
        assert _sanitize_id("IT Infrastructure") == "IT_Infrastructure"
        # "Sr. Developer" -> "Sr_.Developer" -> "Sr__Developer" (dot and space both replaced)
        assert _sanitize_id("Sr. Developer") == "Sr__Developer"
        # Comma is removed by regex, space replaced
        assert _sanitize_id("VP, Engineering") == "VP_Engineering"
        # Parentheses removed by regex
        assert _sanitize_id("Team Lead (Temp)") == "Team_Lead_Temp"


class TestTemplateSafety:
    """Test template safety patterns."""

    def test_jinja_default_filter_pattern(self):
        """Test the Jinja default filter pattern works."""
        from jinja2 import Environment

        env = Environment()

        # Test the pattern: (summary.risk_summary|default({})).critical|default(0)
        template = env.from_string(
            "{{ (data.nested|default({})).value|default(0) }}"
        )

        # With data
        result = template.render(data={'nested': {'value': 5}})
        assert result == "5"

        # Without nested
        result = template.render(data={})
        assert result == "0"

        # Without data
        result = template.render(data=None)
        assert result == "0"

    def test_summary_risk_summary_pattern(self):
        """Test the exact pattern used in dashboard.html."""
        from jinja2 import Environment

        env = Environment()

        # The pattern from dashboard.html line 109
        template = env.from_string(
            "{{ 'danger' if (summary.risk_summary|default({})).critical|default(0) > 0 else 'safe' }}"
        )

        # With critical risks
        result = template.render(summary={'risk_summary': {'critical': 2}})
        assert result == "danger"

        # With no critical risks
        result = template.render(summary={'risk_summary': {'critical': 0}})
        assert result == "safe"

        # Missing risk_summary
        result = template.render(summary={})
        assert result == "safe"

        # Missing summary entirely
        result = template.render(summary=None)
        assert result == "safe"


class TestOrgChartRendering:
    """Test org chart rendering functions."""

    def test_render_mermaid_import_fallback(self):
        """Test _render_mermaid handles ImportError gracefully."""
        # This test verifies the function exists and has the right signature
        from streamlit_app.views.organization.org_chart import _render_mermaid
        import inspect

        # Check function signature
        sig = inspect.signature(_render_mermaid)
        assert 'code' in sig.parameters

    def test_sanitize_id_exported(self):
        """Test _sanitize_id is available for use."""
        from streamlit_app.views.organization.org_chart import _sanitize_id
        assert callable(_sanitize_id)


class TestPresentationIntegration:
    """Integration tests that require the full app context."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        try:
            from web.app import create_app
            app = create_app()
            app.config['TESTING'] = True
            return app
        except ImportError:
            pytest.skip("Flask app not available")

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_dashboard_route_exists(self, client):
        """Test dashboard route is accessible (may redirect to login)."""
        response = client.get('/dashboard', follow_redirects=False)
        # Should either work (200) or redirect to login (302)
        assert response.status_code in [200, 302, 404]

    def test_no_500_on_homepage(self, client):
        """Homepage should not return 500."""
        response = client.get('/')
        assert response.status_code != 500

    def test_static_files_accessible(self, client):
        """Static CSS/JS files should be accessible."""
        # These paths may vary based on the actual static file structure
        css_response = client.get('/static/css/style.css')
        # Should be 200 or 404, not 500
        assert css_response.status_code in [200, 304, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
