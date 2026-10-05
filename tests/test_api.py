"""Tests d'integration des endpoints de l'API, via le TestClient FastAPI."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health_retourne_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "modele_classification_charge" in data


def test_classify_reclamation_valide(client):
    response = client.post(
        "/api/classify",
        json={"text": "Mon colis TRK-2890 est arrive casse."},
    )
    assert response.status_code == 200
    data = response.json()
    assert "categorie" in data
    assert "priorite" in data
    assert "equipe_routage" in data
    assert 0.0 <= data["confiance_categorie"] <= 1.0


def test_classify_texte_vide_retourne_422(client):
    response = client.post("/api/classify", json={"text": ""})
    assert response.status_code == 422


def test_batch_plusieurs_reclamations(client):
    response = client.post(
        "/api/batch",
        json={"texts": ["Colis casse a l'arrivee", "20 jours de retard depuis la commande"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["resultats"]) == 2


def test_batch_lot_trop_volumineux_retourne_400(client):
    response = client.post("/api/batch", json={"texts": ["texte"] * 250})
    assert response.status_code == 400


def test_stats_retourne_200(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_reclamations_traitees" in data


def test_stats_augmente_apres_classification(client):
    stats_avant = client.get("/api/stats").json()["total_reclamations_traitees"]
    client.post("/api/classify", json={"text": "Reclamation de test pour les stats."})
    stats_apres = client.get("/api/stats").json()["total_reclamations_traitees"]
    assert stats_apres == stats_avant + 1
