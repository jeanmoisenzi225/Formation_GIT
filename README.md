# Mon Garage — Gestion des rendez-vous et suivi des travaux

Application web (PWA) dédiée à **un seul garage** en Côte d'Ivoire, pour gérer
la prise de rendez-vous et le suivi des travaux avec ses clients. Chaque
client suit l'avancement des réparations et l'historique d'entretien de ses
véhicules.

Cette application n'est pas une plateforme multi-garages : elle est déployée
et configurée pour un garage précis, avec ses propres clients.

## Périmètre de cette première version (MVP)

- Un seul garage, configuré une fois au premier démarrage (page `/setup`)
- Un compte administrateur pour le garage, qui peut créer des comptes pour
  ses employés (`/garage/staff`)
- Les clients s'inscrivent librement (`/register`)
- Un client peut enregistrer ses véhicules
- Un client peut demander un rendez-vous auprès du garage
- Le garage peut confirmer/refuser un rendez-vous
- Une fois le rendez-vous confirmé, un suivi de travaux est ouvert : le garage
  met à jour le statut (pas commencé / en cours / en attente de pièces /
  terminé) et ajoute des commentaires, visibles par le client
- Le client consulte l'historique complet de chaque véhicule (rendez-vous
  passés + suivi des travaux)

Non inclus dans cette première version (prévu pour la suite) : notifications
temps réel (WebSocket/SMS/email), rappels automatiques d'échéances
d'entretien, recommandations personnalisées.

## Architecture

- `backend/` — API REST en Node.js/TypeScript (Express + Prisma + PostgreSQL)
- `frontend/` — Application web React/TypeScript (Vite), en PWA installable sur mobile
- `docker-compose.yml` — Base de données PostgreSQL pour le développement local

## Démarrage en local

### 1. Base de données

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
cp .env.example .env
npm install
npx prisma migrate dev
npm run dev             # démarre l'API sur http://localhost:4000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev             # démarre l'app sur http://localhost:5173
```

L'application frontend proxifie les appels `/api` vers `http://localhost:4000`
(voir `frontend/vite.config.ts`).

### 4. Configurer le garage (première utilisation uniquement)

Ouvrez `http://localhost:5173/setup` et renseignez les informations du garage
ainsi que le compte administrateur. Cette page ne fonctionne qu'une seule
fois : une fois le garage configuré, l'API refuse toute nouvelle tentative
(409). L'administrateur peut ensuite créer des comptes pour ses employés
depuis `/garage/staff` une fois connecté.

Pour le développement, un script de seed alternatif est aussi disponible et
crée directement un garage et un client de démonstration en base (mot de
passe `password123` pour les deux comptes) :

```bash
cd backend
npm run prisma:seed
```

N'utilisez pas les deux méthodes en même temps : le seed échouera si un
garage existe déjà (et inversement, `/setup` échouera si le seed a déjà été
exécuté).

## Vérifications

```bash
cd backend && npm run typecheck
cd frontend && npm run build
```
