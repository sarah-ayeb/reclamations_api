# API de classification des réclamations

API REST (FastAPI) exposant le pipeline du notebook `reclamations_classification_ameliore` :
nettoyage → classification (TF‑IDF + Logistic Regression) → extraction d'entités (NER
spaCy) → scoring de priorité hybride → routage vers l'équipe compétente.

C'est l'équivalent en service web de la fonction `traiter_reclamation(text)` (section 18
du notebook).

## Endpoints

| Méthode | Route          | Description                                  |
|---------|----------------|-----------------------------------------------|
| POST    | `/api/classify`| Analyse une réclamation unique                |
| POST    | `/api/batch`   | Analyse un lot de réclamations (max 200 par défaut) |
| GET     | `/api/stats`   | Statistiques globales cumulées depuis le démarrage |
| GET     | `/health`      | Santé du service (modèles chargés ou non)     |

Documentation interactive auto-générée : `http://localhost:8000/docs` (Swagger) ou `/redoc`.

## 1. Installer les dépendances

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Déployer les artefacts entraînés du notebook

L'API **ne réentraîne rien** : elle charge les modèles déjà entraînés et sauvegardés
par le notebook (section 15 « Téléchargement des artefacts » / section 18.0
« Rechargement rapide »). Placez-les dans `models/` en respectant cette arborescence :

```
models/
├── baseline_tfidf_logreg_pipeline.joblib   # pipeline sklearn (TfidfVectorizer + LogisticRegression), section 10
└── ner/
    └── model-best/                         # modèle spaCy entraîné, section 16.5
```

Ces chemins sont surchargeables via variables d'environnement si besoin :

```bash
export MODELS_DIR=/chemin/vers/models
# ou individuellement :
export BASELINE_MODEL_PATH=/chemin/vers/baseline_tfidf_logreg_pipeline.joblib
export NER_MODEL_PATH=/chemin/vers/ner/model-best
```

**Comportement en cas de modèle manquant :**
- `baseline_tfidf_logreg_pipeline.joblib` absent → l'API démarre mais `/health` renvoie
  `status: "degraded"` et les endpoints de classification renvoient une erreur `503`
  explicite tant que le fichier n'est pas déposé.
- `ner/model-best` absent → l'API **ne plante pas** : elle bascule automatiquement sur
  une extraction par expressions régulières (numéro de tracking, montant, date — sans
  la VILLE, qui nécessite le modèle appris, cf. section 16.6bis du notebook).
  `/health` indique alors `"ner_mode": "regex_fallback"`.

## 3. Lancer le serveur

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. Exemples d'appels

### Classifier une réclamation

```bash
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "Mon colis TRK-2890 est arrivé à la mauvaise adresse à Sfax, ça fait 5 jours que j'\''attends une solution."}'
```

Réponse :

```json
{
  "reclamation_brute": "Mon colis TRK-2890 est arrivé à la mauvaise adresse à Sfax...",
  "categorie": "ERREUR_DESTINATION",
  "confiance_categorie": 0.83,
  "entites": {"tracking": "TRK-2890", "ville": "Sfax"},
  "priorite": "MOYENNE",
  "score_priorite": 0.34,
  "declencheur_regle_dure": null,
  "equipe_routage": "Logistique",
  "escalade_manager": false
}
```

### Analyser un lot

```bash
curl -X POST http://localhost:8000/api/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Colis cassé à l'\''arrivée", "20 jours de retard depuis la commande"]}'
```

### Statistiques

```bash
curl http://localhost:8000/api/stats
```

Renvoie le total traité, la répartition par catégorie/priorité/équipe, le nombre
d'escalades manager et la confiance moyenne du modèle — cumulés depuis le démarrage
du process (compteurs en mémoire, remis à zéro à chaque redémarrage ; voir
`app/stats.py` pour brancher un backend persistant type Redis si nécessaire).

### Santé

```bash
curl http://localhost:8000/health
```

## Structure du projet

```
reclamations_api/
├── app/
│   ├── main.py          # Application FastAPI, endpoints, orchestration
│   ├── classifier.py    # Chargement/inférence du pipeline TF-IDF + LogReg
│   ├── entities.py      # Extraction NER (spaCy + repli regex)
│   ├── priority.py      # Scoring de priorité hybride (règles + modèle)
│   ├── routing.py        # Table de routage catégorie -> équipe
│   ├── stats.py          # Compteurs en mémoire pour /api/stats
│   ├── schemas.py        # Modèles Pydantic (requêtes/réponses)
│   └── config.py         # Chemins des modèles, constantes
├── models/                # Emplacement attendu des artefacts entraînés (voir §2)
├── requirements.txt
└── README.md
```

## Notes de conception

- Toute la logique métier (nettoyage de texte, mots-clés de priorité, seuils, table de
  routage) est reprise **à l'identique** des sections 5, 17 et 18 du notebook, pour
  garantir des résultats cohérents entre l'exploration et la production.
- `/api/batch` réutilise la même fonction interne que `/api/classify` (pas de logique
  dupliquée) et refuse les lots de plus de `MAX_BATCH_SIZE` (200 par défaut,
  configurable via la variable d'environnement `MAX_BATCH_SIZE`).
- Les statistiques sont actuellement en mémoire (process unique). Pour un déploiement
  avec plusieurs workers/replicas, remplacez `app/stats.py` par un backend partagé.
