# Analyseur de portefeuille titres

Application web qui analyse un relevé de compte-titres (export CSV d'un courtier) et confronte les positions aux données de marché en temps réel : valorisation, répartition, performance vs indices, indicateurs de risque.

## Architecture

```
backend/    API FastAPI (Python) — parsing CSV, calcul du portefeuille, données de marché (yfinance), analytics
frontend/   Dashboard React + TypeScript (Vite) — upload, tableaux, graphiques
```

Le frontend envoie le fichier CSV à `POST /api/analyze`, qui renvoie en une seule réponse : positions valorisées, répartition (secteur/pays/titre), courbe de performance vs benchmarks (CAC 40, S&P 500, MSCI World) et indicateurs de risque (volatilité, Sharpe, drawdown max). Aucune donnée n'est persistée côté serveur : tout est recalculé à la volée à chaque analyse.

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

Un relevé d'exemple est fourni dans `backend/sample_data/releve_exemple.csv` pour tester l'application de bout en bout.

## Format du relevé CSV attendu

Le parseur (`backend/app/parser.py`) reconnaît plusieurs libellés de colonnes (français/anglais) pour s'adapter à différents exports de courtiers. Colonnes obligatoires : **date**, **ticker**, **quantité**. Colonnes optionnelles : libellé, type, prix unitaire (ou montant), frais, devise.

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

**Important : le champ `ticker` doit être un symbole reconnu par Yahoo Finance** (ex. `AAPL`, `MC.PA`, `AI.PA`), pas un code ISIN — Yahoo Finance ne fait pas de résolution ISIN → ticker de façon fiable. Si un titre n'est pas reconnu, sa position reste affichée au coût d'achat avec un avertissement, sans faire échouer le reste de l'analyse.

Exemple minimal :

```csv
Date;Ticker;Libellé;Type;Quantité;Cours;Frais;Devise
15/01/2023;AAPL;Apple Inc.;Achat;10;135.21;4.99;USD
```

## Fonctionnalités

- **Valorisation ligne par ligne** : coût moyen pondéré, valeur actuelle, plus/moins-value latente, poids dans le portefeuille, P/E.
- **Répartition & diversification** : par secteur, par zone géographique, par titre.
- **Performance vs marché** : reconstruction de la valeur du portefeuille dans le temps, comparée au CAC 40, au S&P 500 et au MSCI World (base 100).
- **Indicateurs de risque** : volatilité annualisée, ratio de Sharpe (taux sans risque 2 %), drawdown maximum.
- **Plus-values réalisées, dividendes et frais** cumulés sur l'historique des transactions.

## Tests

```bash
cd backend
pytest
```

Les tests couvrent le parsing CSV, le calcul des positions (coût moyen pondéré, ventes, dividendes) et les analytics (allocation, performance, risque), avec les appels réseau vers Yahoo Finance mockés — ils s'exécutent donc sans connexion internet.

## Limitation connue

Les prix et données fondamentales proviennent de Yahoo Finance via `yfinance`, un service public non garanti qui peut occasionnellement renvoyer des erreurs de limitation (429) en cas de pic de requêtes. Dans ce cas, l'application dégrade proprement : les positions concernées restent affichées au coût d'achat avec un avertissement explicite, plutôt que de faire échouer l'analyse.
