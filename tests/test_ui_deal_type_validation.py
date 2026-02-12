"""
Test UI-level deal type validation

Tests validation at multiple layers:
- UI form validation (simulated)
- API endpoint validation
- Database constraint enforcement
- Deal type update functionality
"""

import pytest
from web.database import db, Deal
from web.routes.deals import deals_bp


class TestDealTypeValidation:
    """Test UI-level deal type validation."""

    @pytest.fixture
    def client(self, app):
        """Flask test client."""
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from web.app import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()

    def test_create_deal_without_type_fails(self, client):
        """Test that creating deal without deal_type is rejected."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co'
            # deal_type is MISSING
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'deal type is required' in data['error'].lower()

    def test_create_deal_with_empty_type_fails(self, client):
        """Test that empty deal_type is rejected."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co',
            'deal_type': ''  # Empty string
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'deal type is required' in data['error'].lower()

    def test_create_deal_with_invalid_type_fails(self, client):
        """Test that invalid deal_type is rejected."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co',
            'deal_type': 'merger'  # Invalid (not in allowed list)
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'invalid deal type' in data['error'].lower()

    def test_create_deal_with_acquisition_succeeds(self, client):
        """Test that valid deal_type 'acquisition' is accepted."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co',
            'deal_type': 'acquisition'  # Valid
        })

        assert response.status_code == 201
        data = response.get_json()
        assert 'deal' in data
        assert data['deal']['deal_type'] == 'acquisition'
        assert 'created successfully' in data['message'].lower()

    def test_create_deal_with_carveout_succeeds(self, client):
        """Test that valid deal_type 'carveout' is accepted."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co',
            'deal_type': 'carveout'  # Valid
        })

        assert response.status_code == 201
        data = response.get_json()
        assert 'deal' in data
        assert data['deal']['deal_type'] == 'carveout'

    def test_create_deal_with_divestiture_succeeds(self, client):
        """Test that valid deal_type 'divestiture' is accepted."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co',
            'deal_type': 'divestiture'  # Valid
        })

        assert response.status_code == 201
        data = response.get_json()
        assert 'deal' in data
        assert data['deal']['deal_type'] == 'divestiture'

    def test_update_deal_type_with_invalid_type_fails(self, client, app):
        """Test that updating to invalid deal_type is rejected."""
        # Create a deal first
        with app.app_context():
            deal = Deal(
                name='Test Deal',
                target_name='Target Co',
                deal_type='acquisition'
            )
            db.session.add(deal)
            db.session.commit()
            deal_id = deal.id

        # Try to update with invalid type
        response = client.patch(f'/api/deals/{deal_id}', json={
            'deal_type': 'merger'  # Invalid
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'invalid deal type' in data['error'].lower()

    def test_update_deal_type_endpoint(self, client, app):
        """Test the dedicated update_deal_type endpoint."""
        # Create a deal first
        with app.app_context():
            deal = Deal(
                name='Test Deal',
                target_name='Target Co',
                deal_type='acquisition'
            )
            db.session.add(deal)
            db.session.commit()
            deal_id = deal.id

        # Update deal type
        response = client.post(f'/api/deals/{deal_id}/update_type', json={
            'deal_type': 'carveout'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['deal']['deal_type'] == 'carveout'
        assert 're-run analysis' in data['message'].lower()

    def test_update_deal_type_logs_change(self, client, app):
        """Test that changing deal type is logged properly."""
        # Create a deal
        with app.app_context():
            deal = Deal(
                name='Test Deal',
                target_name='Target Co',
                deal_type='acquisition'
            )
            db.session.add(deal)
            db.session.commit()
            deal_id = deal.id

        # Update deal type
        response = client.post(f'/api/deals/{deal_id}/update_type', json={
            'deal_type': 'divestiture'
        })

        assert response.status_code == 200
        data = response.get_json()
        # Message should indicate the change
        assert 'acquisition' in data['message'].lower()
        assert 'divestiture' in data['message'].lower()

    def test_database_constraint_enforcement(self, app):
        """Test that database CHECK constraint rejects invalid values."""
        with app.app_context():
            deal = Deal(
                name='Test Deal',
                target_name='Target Co',
                deal_type='invalid_type'  # Should fail CHECK constraint
            )
            db.session.add(deal)

            with pytest.raises(Exception):  # IntegrityError or similar
                db.session.commit()

            db.session.rollback()

    def test_database_not_null_constraint(self, app):
        """Test that database NOT NULL constraint rejects NULL values."""
        with app.app_context():
            deal = Deal(
                name='Test Deal',
                target_name='Target Co',
                deal_type=None  # Should fail NOT NULL constraint
            )
            db.session.add(deal)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

            db.session.rollback()

    def test_all_valid_deal_types(self, client):
        """Test that all valid deal types are accepted."""
        valid_types = ['acquisition', 'carveout', 'divestiture']

        for deal_type in valid_types:
            response = client.post('/api/deals', json={
                'name': f'Test Deal - {deal_type}',
                'target_name': 'Target Co',
                'buyer_name': 'Buyer Co',
                'deal_type': deal_type
            })

            assert response.status_code == 201, f"Failed for deal_type: {deal_type}"
            data = response.get_json()
            assert data['deal']['deal_type'] == deal_type

    def test_case_sensitivity(self, client):
        """Test that deal_type is case-sensitive (lowercase required)."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co',
            'deal_type': 'ACQUISITION'  # Uppercase should fail
        })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_whitespace_handling(self, client):
        """Test that whitespace is properly trimmed."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'buyer_name': 'Buyer Co',
            'deal_type': '  acquisition  '  # Whitespace should be trimmed
        })

        # Should succeed after trimming
        assert response.status_code == 201
        data = response.get_json()
        assert data['deal']['deal_type'] == 'acquisition'


class TestDealTypeMessages:
    """Test that error messages are clear and helpful."""

    @pytest.fixture
    def client(self, app):
        """Flask test client."""
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from web.app import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()

    def test_missing_deal_type_message(self, client):
        """Test error message for missing deal_type."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co'
        })

        data = response.get_json()
        assert 'Deal type is required' in data['error']
        assert 'Acquisition' in data['error']
        assert 'Carve-Out' in data['error']
        assert 'Divestiture' in data['error']

    def test_invalid_deal_type_message(self, client):
        """Test error message for invalid deal_type."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'deal_type': 'merger'
        })

        data = response.get_json()
        assert 'Invalid deal type' in data['error']
        assert 'merger' in data['error']
        assert 'acquisition' in data['error']
        assert 'carveout' in data['error']
        assert 'divestiture' in data['error']

    def test_success_message_includes_deal_type(self, client):
        """Test that success message confirms the deal type."""
        response = client.post('/api/deals', json={
            'name': 'Test Deal',
            'target_name': 'Target Co',
            'deal_type': 'carveout'
        })

        data = response.get_json()
        assert 'CARVEOUT' in data['message']
        assert 'created successfully' in data['message'].lower()
