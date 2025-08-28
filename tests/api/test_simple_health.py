"""Simple tests for health endpoints to increase coverage."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock

from autobox.api.routes.health import router


class TestSimpleHealth:
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with health router."""
        app = FastAPI()
        app.include_router(router)
        
        # Add mock state
        app.state.simulation_cache = {"last_updated": "2024-01-01T00:00:00"}
        app.state.actor_manager = Mock()
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_ping(self, client):
        """Test ping endpoint."""
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.text == '"pong"'
    
    def test_health(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["server"] == "healthy"
        assert data["actor_connected"] is True
        assert data["cache_status"] == "active"
    
    def test_health_no_cache(self):
        """Test health check with no cache update."""
        app = FastAPI()
        app.include_router(router)
        app.state.simulation_cache = {}
        app.state.actor_manager = None
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["actor_connected"] is False
        assert data["cache_status"] == "waiting"