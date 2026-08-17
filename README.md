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

## Déploiement (URL publique gratuite)

L'app n'est hébergée nulle part par défaut. Voici comment obtenir une URL publique en ~10 minutes avec Render (backend) + Vercel (frontend) — les deux ont un plan gratuit et se connectent directement au repo GitHub. Ces comptes t'appartiennent : je ne peux pas les créer à ta place, mais tout est préparé pour que ce soit juste quelques clics.

**1. Backend sur Render**
1. Créer un compte sur [render.com](https://render.com) (gratuit, connexion via GitHub).
2. « New + » → « Blueprint » → sélectionner le repo `jeanmoisenzi225/Formation_GIT`, branche `claude/portfolio-analysis-app-movgid`.
3. Render détecte `render.yaml` à la racine et propose de créer le service `portfolio-analyzer-api` → cliquer « Apply ».
4. Attendre la fin du build (2-3 min), puis noter l'URL générée (ex. `https://portfolio-analyzer-api-xxxx.onrender.com`).

Le plan gratuit met le service en veille après 15 min d'inactivité : la première requête après une pause prend 30-60 s (cold start), ensuite c'est rapide.

**2. Frontend sur Vercel**
1. Créer un compte sur [vercel.com](https://vercel.com) (gratuit, connexion via GitHub).
2. « Add New » → « Project » → importer le même repo et la même branche.
3. Dans « Root Directory », sélectionner `frontend` (Vercel détecte Vite automatiquement).
4. Ajouter la variable d'environnement `VITE_API_BASE_URL` = l'URL Render obtenue à l'étape 1.
5. Déployer → Vercel donne une URL du type `https://xxxx.vercel.app`.

**3. Autoriser le frontend sur le backend**
Retourner sur Render → Environment → remplacer `CORS_ORIGINS` (valeur par défaut `http://localhost:5173`) par l'URL Vercel obtenue, puis redéployer le service.

L'app est alors accessible à l'URL Vercel pour n'importe qui possédant le lien. Chaque nouveau `git push` sur cette branche redéploie automatiquement les deux services.

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
