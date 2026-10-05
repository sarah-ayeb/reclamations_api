"""Tests unitaires du module d'extraction d'entites (app/entities.py), repli regex."""
from app.entities import EntityExtractor


def test_extraction_tracking_prefixe_generique():
    extractor = EntityExtractor(model_path="modele_inexistant")
    assert extractor.using_fallback is True
    resultat = extractor.extract("Ma commande CMR-2023-99463 n'est jamais arrivee.")
    assert resultat.get("tracking") == "CMR-2023-99463"


def test_extraction_montant_devise_tunisienne():
    extractor = EntityExtractor(model_path="modele_inexistant")
    resultat = extractor.extract("Je veux etre rembourse 516,90 DT.")
    assert "montant" in resultat
    assert "DT" in resultat["montant"]


def test_extraction_aucune_entite():
    extractor = EntityExtractor(model_path="modele_inexistant")
    resultat = extractor.extract("Bonjour, question generale sur vos horaires.")
    assert resultat == {}
