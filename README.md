# Analyseur de portefeuille titres — BRVM

Application web qui analyse un relevé de compte-titres (export CSV d'un courtier) et confronte les positions aux données de marché en temps réel : valorisation, répartition, performance vs indices, indicateurs de risque.

Conçue en priorité pour les portefeuilles **BRVM** (Bourse Régionale des Valeurs Mobilières — Bénin, Burkina Faso, Côte d'Ivoire, Guinée-Bissau, Mali, Niger, Sénégal, Togo). Un titre non coté à la BRVM (ex. `AAPL`) reste géré via Yahoo Finance en repli, pour un portefeuille mixte.

## Architecture

```
backend/    API FastAPI (Python) — parsing CSV, calcul du portefeuille, données de marché, analytics
frontend/   Dashboard React + TypeScript (Vite) — upload, tableaux, graphiques
```

Le frontend envoie le fichier CSV à `POST /api/analyze`, qui renvoie en une seule réponse : positions valorisées, répartition (secteur/pays/titre), courbe de performance vs benchmarks BRVM et indicateurs de risque (volatilité, Sharpe, drawdown max). Aucune donnée n'est persistée côté serveur : tout est recalculé à la volée à chaque analyse.

### Sources de données BRVM

Il n'existe pas d'API officielle gratuite pour la BRVM. L'application combine deux sources publiques, scrapées défensivement (toute panne dégrade en avertissement plutôt que de faire échouer l'analyse) :

| Donnée | Source | Détail |
|---|---|---|
| Cours du jour, tous titres | [brvm.org](https://www.brvm.org) `/fr/cours-actions/0` | 1 requête HTTP couvre l'ensemble des titres cotés |
| Classification sectorielle | brvm.org, 7 pages sectorielles | Conso de base, Conso discrétionnaire, Énergie, Industriels, Services financiers, Services publics, Télécoms |
| Capitalisations | brvm.org `/fr/capitalisations/0` | Nombre de titres, capitalisation flottante/globale |
| Indices (BRVM Composite, BRVM 30) — niveau du jour | brvm.org `/fr/indices` | |
| **Historique quotidien** (cours + indices) | [sikafinance.com](https://www.sikafinance.com), endpoint JSON `POST /api/general/GetHistos` | Fenêtre max. 3 mois par requête → paginé côté backend, fetch parallélisé par titre |

Le référentiel des titres BRVM (code ↔ pays ↔ secteur) est codé en dur dans `backend/app/brvm_reference.py` (~45 sociétés cotées) car les nouvelles introductions en bourse sont rares. À rafraîchir manuellement si un ticker d'un relevé n'est pas reconnu.

**P/E non disponible** : ni brvm.org ni sikafinance ne publient de ratio cours/bénéfice exploitable par scraping ; le champ reste vide pour les titres BRVM.

## Démarrage rapide

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

L'API est alors disponible sur `http://localhost:8000` (doc interactive sur `/docs`).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL pointe vers le backend
npm run dev
```

Le dashboard est accessible sur `http://localhost:5173`.

Un relevé d'exemple est fourni dans `backend/sample_data/releve_exemple.csv` (titres BRVM réels : Ecobank CI, Sonatel, Sodeci, Bank of Africa Bénin, Orange CI) pour tester l'application de bout en bout.

## Format du relevé CSV attendu

Le parseur (`backend/app/parser.py`) reconnaît plusieurs libellés de colonnes (français/anglais) pour s'adapter à différents exports de courtiers. Colonnes obligatoires : **date**, **ticker**, **quantité**. Colonnes optionnelles : libellé, type, prix unitaire (ou montant), frais, devise (XOF par défaut).

| Champ | Alias reconnus |
|---|---|
| date | date, date opération, date d'opération, trade date |
| ticker | ticker, symbol, code, isin |
| libellé | libellé, nom, name, désignation, titre |
| type | type, sens, opération, achat/vente/dividende/frais |
| quantité | quantité, quantity, qté, nombre de titres |
| prix unitaire | prix, cours, price, prix unitaire |
| montant (fallback) | montant, montant net, amount, total |
| frais | frais, commission, fees |
| devise | devise, currency |

**Le champ `ticker` doit être le code BRVM du titre** (ex. `ECOC`, `SNTS`, `SDCC` — pas un code ISIN, la résolution ISIN → ticker n'est pas fiable). La liste complète des codes reconnus est dans `backend/app/brvm_reference.py`. Un titre hors BRVM (ex. `AAPL`, `MC.PA`) est tenté via Yahoo Finance. Si un titre n'est reconnu par aucune des deux sources, sa position reste affichée au coût d'achat avec un avertissement, sans faire échouer le reste de l'analyse.

Exemple minimal :

```csv
Date;Ticker;Libellé;Type;Quantité;Cours;Frais;Devise
15/01/2024;ECOC;Ecobank Côte d'Ivoire;Achat;50;6800;2500;XOF
```

## Fonctionnalités

- **Valorisation ligne par ligne** : coût moyen pondéré, valeur actuelle, plus/moins-value latente, poids dans le portefeuille.
- **Répartition & diversification** : par secteur, par zone géographique (pays UEMOA), par titre.
- **Performance vs marché** : reconstruction de la valeur du portefeuille dans le temps, comparée au BRVM Composite et au BRVM 30 (base 100).
- **Indicateurs de risque** : volatilité annualisée, ratio de Sharpe (taux sans risque 2 %), drawdown maximum.
- **Plus-values réalisées, dividendes et frais** cumulés sur l'historique des transactions.

## Tests

```bash
cd backend
pytest
```

Les tests couvrent le parsing CSV, le calcul des positions (coût moyen pondéré, ventes, dividendes), le référentiel BRVM et les analytics (allocation, performance, risque), avec les appels réseau mockés — ils s'exécutent donc sans connexion internet.

## Limitations connues

- **brvm.org / sikafinance ne sont pas des API officielles** : ce sont des sites publics scrapés, sans garantie de disponibilité ni de stabilité de structure. En cas de panne ou de changement de mise en page, l'application dégrade proprement (position affichée au coût d'achat + avertissement explicite) plutôt que d'échouer.
- **Historique limité à 3 ans** par défaut pour la courbe de performance, afin de garder l'analyse réactive (nombre de requêtes paginées vers sikafinance sinon trop élevé).
- **P/E indisponible** pour les titres BRVM (voir plus haut).
- **Référentiel de titres à rafraîchir manuellement** en cas de nouvelle introduction en bourse à la BRVM.
