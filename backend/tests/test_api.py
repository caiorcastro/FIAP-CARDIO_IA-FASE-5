import os

import pytest


@pytest.fixture()
def client(monkeypatch):
    # Testes não devem depender de credenciais reais.
    monkeypatch.setenv("CARDIOIA_ASSISTANT_MODE", "local")
    from backend.app import create_app

    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_status_ok(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "assistant" in data
    assert data["assistant"] in ["local", "watson"]


def test_message_blank_is_conversational(client):
    res = client.post("/api/message", json={"message": "   ", "user_id": "u1"})
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data.get("response"), str)
    # Não deve ser erro 400; deve orientar o usuário.
    assert "posso te ajudar" in data["response"].lower()


def test_message_roundtrip_mock(client):
    res1 = client.post("/api/message", json={"message": "Olá", "user_id": "u2"})
    assert res1.status_code == 200
    data1 = res1.get_json()
    assert isinstance(data1.get("response"), str)
    assert data1["response"].strip() != ""

    res2 = client.post("/api/message", json={"message": "Quero agendar uma consulta", "user_id": "u2"})
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert isinstance(data2.get("response"), str)
    assert data2["response"].strip() != ""
