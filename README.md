# Garages CI — Gestion des rendez-vous et suivi des travaux

Application web (PWA) permettant à des garages en Côte d'Ivoire de gérer la prise
de rendez-vous et le suivi des travaux, et permettant aux clients de suivre
l'avancement des réparations et l'historique d'entretien de leurs véhicules.

## Périmètre de cette première version (MVP)

- Comptes garages (administrateur) et comptes clients
- Un client peut enregistrer ses véhicules
- Un client peut demander un rendez-vous auprès d'un garage
- Un garage peut confirmer/refuser un rendez-vous
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
npx prisma migrate dev --name init
npm run prisma:seed   # crée un garage et un client de démonstration
npm run dev            # démarre l'API sur http://localhost:4000
```

Compte de démonstration créé par le seed (mot de passe : `password123`) :

- Garage : `admin@garage-plateau.ci`
- Client : `client@example.ci`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev             # démarre l'app sur http://localhost:5173
```

L'application frontend proxifie les appels `/api` vers `http://localhost:4000`
(voir `frontend/vite.config.ts`).

## Vérifications

```bash
cd backend && npm run typecheck
cd frontend && npm run build
```
