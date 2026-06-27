import pytest

from app.main import app
import app.routers.providers as providers_router


def get_test_client():
    pytest.importorskip("httpx2")
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_settings_roundtrip_persists_model_configs(tmp_path, monkeypatch):
    monkeypatch.setattr(providers_router, "SETTINGS_PATH", tmp_path / "settings.json")
    client = get_test_client()
    settings = {
        "settingsVersion": 2,
        "theme": "light",
        "llmConfigs": [
            {
                "id": "llm-1",
                "name": "LLM",
                "apiUrl": "https://api.example.com/v1",
                "apiKey": "key",
                "model": "model",
                "enabled": True,
            }
        ],
        "imageConfigs": [],
        "visionConfigs": [],
        "selectedLlmConfigId": "llm-1",
        "selectedImageConfigId": "",
        "selectedVisionConfigId": "",
        "providers": [],
    }

    save_response = client.post("/api/settings", json=settings)

    assert save_response.status_code == 200
    assert save_response.json()["ok"] is True
    assert client.get("/api/settings").json()["settings"] == settings
