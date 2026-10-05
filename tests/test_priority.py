"""Tests unitaires du module de scoring de priorite (app/priority.py)."""
from app.priority import score_priority


def test_dommage_majeur_declenche_priorite_haute():
    resultat = score_priority(
        "Le produit a explose et je me suis brule la main, tres grave.",
        "PRODUIT_ENDOMMAGE",
    )
    assert resultat["priorite"] == "HAUTE"
    assert resultat["declencheur_regle_dure"] == "dommage_majeur"
    assert resultat["score"] == 1.0


def test_perte_vol_declenche_priorite_haute():
    resultat = score_priority(
        "Mon colis a ete vole, plus de nouvelles depuis une semaine.",
        "PERTE_VOL",
    )
    assert resultat["priorite"] == "HAUTE"
    assert resultat["declencheur_regle_dure"] == "perte_vol_confirme"


def test_retard_urgent_declenche_priorite_haute():
    resultat = score_priority(
        "Cela fait 20 jours de retard sur ma commande.",
        "RETARD_LIVRAISON",
    )
    assert resultat["priorite"] == "HAUTE"
    assert resultat["declencheur_regle_dure"] == "retard_urgent"


def test_reclamation_neutre_priorite_basse():
    resultat = score_priority(
        "Bonjour, je voudrais des informations sur vos tarifs.",
        "AUTRE",
        model_confidence=0.6,
    )
    assert resultat["priorite"] == "BASSE"
    assert resultat["declencheur_regle_dure"] is None


def test_montant_eleve_augmente_le_score():
    resultat = score_priority(
        "Je demande un remboursement de 1500 euros pour mon achat.",
        "RETOUR_REMBOURSEMENT",
        model_confidence=0.7,
    )
    assert resultat["score"] > 0.0
    assert resultat["declencheur_regle_dure"] is None


def test_extraction_montant_devise_dinar():
    from app.priority import extraire_montant_eur

    assert extraire_montant_eur("Le montant est de 516,90 DT.") == 516.90
    assert extraire_montant_eur("Cela coute 1095DT au total.") == 1095.0
