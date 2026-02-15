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


def test_phase2_triage_endpoint(client):
    res = client.post("/api/phase2/triage", json={"text": "Estou com dor no peito e falta de ar"})
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data.get("risk"), str)
    assert "diagnosis" in data


def test_clinical_extract_fallback_local(client, monkeypatch):
    # Sem chave Gemini, deve funcionar com fallback local.
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    res = client.post("/api/clinical/extract", json={"text": "Minha pressao esta 150/95 e FC 88 bpm"})
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("source") in ["local", "gemini"]
    assert isinstance(data.get("structured"), dict)
    assert "triage" in data


def test_monitor_logs_endpoint_empty_ok(client):
    res = client.get("/api/monitor/logs")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data.get("logs"), list)


def test_local_dor_no_braco_nao_dispara_emergencia(client):
    # Regressao: "dor no braço" nao pode virar "dor no peito" por similaridade com exemplos.
    uid = "u_braco"
    res = client.post("/api/message", json={"message": "to com dor no braço", "user_id": uid})
    assert res.status_code == 200
    txt = (res.get_json().get("response") or "").lower()
    assert "dor no peito" not in txt
    assert ("esquerdo" in txt) or ("direito" in txt)


def test_local_emergencia_aceita_resposta_livre_sem_travar(client):
    uid = "u_emerg"
    r1 = client.post("/api/message", json={"message": "estou com dor no peito", "user_id": uid})
    assert r1.status_code == 200
    t1 = (r1.get_json().get("response") or "").lower()
    assert "sim" in t1 and "não" in t1  # pergunta binaria

    # Resposta "humana" (nao binaria) deve ser interpretada e o fluxo deve avançar.
    r2 = client.post("/api/message", json={"message": "no direito", "user_id": uid})
    assert r2.status_code == 200
    t2 = (r2.get_json().get("response") or "").lower()
    assert "falta de ar" in t2

    # Mesmo fora do sim/nao, o bot deve sair do loop e oferecer um caminho (ex: agendamento).
    r3 = client.post("/api/message", json={"message": "onde eu acho um médico????", "user_id": uid})
    assert r3.status_code == 200
    t3 = (r3.get_json().get("response") or "").lower()
    assert ("pré-agendar" in t3) or ("agendar" in t3)
