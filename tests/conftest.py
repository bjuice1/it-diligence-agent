"""
Pytest configuration and shared fixtures for deal type awareness testing.

Provides common test fixtures, database setup, and test utilities.
"""

import pytest
import tempfile
import os
from pathlib import Path
from web.database import db as _db, Deal
from flask import Flask


@pytest.fixture(scope='session')
def app():
    """Create Flask application for testing."""
    app = Flask(__name__)

    # Use in-memory SQLite for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True

    # Initialize database
    _db.init_app(app)

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def db_session(app):
    """Create a new database session for a test.

    Automatically rolls back changes after each test.
    """
    with app.app_context():
        # Begin a transaction
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Bind session to connection
        options = dict(bind=connection, binds={})
        session = _db.create_scoped_session(options=options)

        _db.session = session

        yield session

        # Rollback transaction
        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def sample_acquisition_deal(db_session):
    """Create a sample acquisition deal for testing."""
    deal = Deal(
        name="Test Acquisition",
        target_name="Target Corp",
        buyer_name="Buyer Corp",
        deal_type="acquisition"
    )
    db_session.add(deal)
    db_session.commit()

    yield deal

    # Cleanup
    db_session.delete(deal)
    db_session.commit()


@pytest.fixture
def sample_carveout_deal(db_session):
    """Create a sample carveout deal for testing."""
    deal = Deal(
        name="Test Carveout",
        target_name="Carved Division",
        buyer_name="NewCo",
        deal_type="carveout"
    )
    db_session.add(deal)
    db_session.commit()

    yield deal

    # Cleanup
    db_session.delete(deal)
    db_session.commit()


@pytest.fixture
def sample_divestiture_deal(db_session):
    """Create a sample divestiture deal for testing."""
    deal = Deal(
        name="Test Divestiture",
        target_name="Divested Unit",
        buyer_name="Acquirer",
        deal_type="divestiture"
    )
    db_session.add(deal)
    db_session.commit()

    yield deal

    # Cleanup
    db_session.delete(deal)
    db_session.commit()


@pytest.fixture
def all_deal_types(db_session):
    """Create deals for all three deal types."""
    deals = {
        'acquisition': Deal(
            name="Test Acquisition",
            target_name="Target",
            deal_type="acquisition"
        ),
        'carveout': Deal(
            name="Test Carveout",
            target_name="Target",
            deal_type="carveout"
        ),
        'divestiture': Deal(
            name="Test Divestiture",
            target_name="Target",
            deal_type="divestiture"
        )
    }

    for deal in deals.values():
        db_session.add(deal)

    db_session.commit()

    yield deals

    # Cleanup
    for deal in deals.values():
        db_session.delete(deal)
    db_session.commit()


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_documents():
    """Provide sample document paths for E2E testing."""
    # Return empty list for now - tests can override if needed
    return []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "regression: marks tests as regression tests"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark e2e tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)

        # Mark regression tests
        if "regression" in str(item.fspath):
            item.add_marker(pytest.mark.regression)
