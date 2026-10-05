"""Tests unitaires du module de routage (app/routing.py)."""
from app.routing import router_equipe


def test_routage_perte_vol_vers_logistique():
    resultat = router_equipe("PERTE_VOL")
    assert resultat["equipe"] == "Logistique"
    assert resultat["escalade_manager"] is False


def test_routage_categorie_inconnue_vers_support_general():
    resultat = router_equipe("CATEGORIE_INEXISTANTE")
    assert resultat["equipe"] == "Support général"


def test_declencheur_dommage_majeur_provoque_escalade():
    resultat = router_equipe("PRODUIT_ENDOMMAGE", declencheur_regle_dure="dommage_majeur")
    assert resultat["escalade_manager"] is True


def test_declencheur_perte_vol_ne_provoque_pas_escalade_supplementaire():
    resultat = router_equipe("PERTE_VOL", declencheur_regle_dure="perte_vol_confirme")
    assert resultat["escalade_manager"] is False
