# Agent WhatsApp - Actualités BRVM

Agent qui surveille le site officiel de la BRVM (Bourse Régionale des
Valeurs Mobilières, `www.brvm.org`) et envoie automatiquement des messages
WhatsApp :

1. **Alertes news** : dès qu'une nouvelle annonce/communiqué est publiée par
   la BRVM ou une société cotée (communiqués de presse, franchissements de
   seuil, changements de dirigeants, notations financières...).
2. **Récapitulatif de clôture** : une fois par jour, après la fin de la
   séance de cotation, un résumé chiffré (BRVM Composite, BRVM 30,
   capitalisation, volumes, plus fortes hausses/baisses) accompagné du
   **Bulletin Officiel de la Cote (BOC)** officiel en PDF.
3. **Assistant conversationnel** : l'utilisateur peut écrire n'importe quoi
   sur WhatsApp ("quoi de beau aujourd'hui ?", "et SONATEL, ça donne quoi ?"...)
   et recevoir une réponse en langage naturel, générée par Claude et
   contextualisée avec les données BRVM les plus récentes.

**Abonnement automatique** : il n'y a rien à configurer manuellement pour
qu'une nouvelle personne reçoive les alertes. Le **premier message qu'elle
envoie** au numéro WhatsApp Business suffit à l'abonner (voir
`brvm_agent/subscribers.py`). Elle peut se désabonner à tout moment en
écrivant `STOP`.

> ⚠️ **Important** : WhatsApp ne notifie jamais une entreprise quand
> quelqu'un l'ajoute à ses contacts — seul un **message envoyé** déclenche
> quelque chose côté serveur. C'est pour ça que l'abonnement se fait par un
> premier message, pas par un simple ajout au répertoire. Pour rendre ça
> immédiat côté utilisateur (5 min max), partagez un lien
> `https://wa.me/<numero>?text=ABONNEMENT` (ou son QR code) : un tap ouvre
> WhatsApp avec le message pré-rempli, il suffit d'appuyer sur Envoyer.

Le guide pas-à-pas complet (déploiement + abonnement) est dans
`GUIDE_DEPLOIEMENT.pdf` (régénérable via `tools/build_guide_pdf.py`,
`pip install -r requirements-docs.txt` puis
`python tools/build_guide_pdf.py`).

Depuis la version actuelle, un **seul process** (`webhook_server.py`) gère
tout : réponses conversationnelles, alertes news et recap BOC automatiques
(planificateur intégré, voir `brvm_agent/scheduler.py`). Les scripts
`check_news.py`/`send_recap.py` restent disponibles pour un usage en cron
externe si vous préférez ne pas utiliser le planificateur intégré
(`ENABLE_SCHEDULER=false`).

## Comment ça marche

Le site `brvm.org` ne propose pas de flux RSS/API public. L'agent scrute
donc directement les pages HTML publiques du site :

- Annonces : `https://www.brvm.org/fr/emetteurs/type-annonces/<categorie>`
  (ex : `communiques`, `franchissements-de-seuil`, `changements-de-dirigeants`,
  `notations-financieres`). Ce sont des tableaux (date / société / titre /
  lien PDF) mis à jour par la BRVM au fil de l'eau.
- BOC : `https://www.brvm.org/fr/bulletins-officiels-de-la-cote` liste les
  bulletins PDF quotidiens, du plus récent au plus ancien. La 1ère page du
  PDF contient toujours un résumé chiffré de la séance, que l'agent extrait
  automatiquement (`brvm_agent/boc.py`).

Un fichier `state.json` local mémorise les annonces déjà envoyées et la date
du dernier BOC transmis, pour ne jamais envoyer deux fois le même message.

**Attention** : ce sont des pages HTML publiques, pas une API officielle.
Si la BRVM change la mise en page de son site, les sélecteurs dans
`brvm_agent/news.py` et `brvm_agent/boc.py` devront être mis à jour (ils
sont volontairement défensifs : un champ non trouvé devient `None` plutôt
que de faire planter tout l'envoi).

## Pourquoi WhatsApp Cloud API (Meta) ?

C'est la seule solution officielle et pérenne pour envoyer des messages
WhatsApp automatiques (les librairies non officielles type `whatsapp-web.js`
simulent un téléphone connecté et violent les CGU de WhatsApp — risque de
bannissement du numéro).

**Point important** : Meta impose que tout message envoyé **en dehors des
24h suivant le dernier message reçu du destinataire** utilise un
**message template pré-approuvé**. Comme cet agent envoie des messages non
sollicités au quotidien, il faut créer et faire approuver des templates.

### Mise en place (une seule fois)

1. Créer une app sur [developers.facebook.com](https://developers.facebook.com/)
   avec le produit **WhatsApp**, et un numéro WhatsApp Business (un numéro
   de test suffit pour commencer).
2. Récupérer `WHATSAPP_TOKEN` (jeton d'accès) et `WHATSAPP_PHONE_NUMBER_ID`.
   **Pour un fonctionnement continu (h24)**, il faut un jeton **permanent** :
   le jeton "temporaire" affiché par défaut expire au bout de 24h, ce qui
   casserait l'agent le lendemain. Créer un jeton permanent via Meta
   Business Suite > Paramètres de l'entreprise > Utilisateurs système >
   Ajouter un utilisateur système (rôle Admin) > Générer un nouveau jeton
   avec la permission `whatsapp_business_messaging` (et
   `whatsapp_business_management`) et une expiration "Jamais". Détails
   pas-à-pas dans `GUIDE_DEPLOIEMENT.pdf`.
3. Dans Meta Business Manager > WhatsApp Manager > Modèles de message,
   créer deux templates (catégorie **Utility**) :
   - `brvm_news_alert` (corps avec 3 variables), par exemple :
     > 📈 BRVM - Nouvelle annonce
     > Société : {{1}}
     > {{2}}
     > 🔗 {{3}}
   - `brvm_boc_recap` (en-tête **Document** + corps avec 3 variables), par
     exemple :
     > En-tête : Document (dynamique)
     > Corps :
     > 📊 {{1}}
     > BRVM Composite : {{2}}
     > BRVM 30 : {{3}}
     > Le bulletin officiel complet est joint à ce message.
   - Soumettre les deux templates à validation Meta (généralement quelques
     minutes à quelques heures).
4. Ajouter les destinataires (numéros au format international, ex.
   `2250700000000`) à `WHATSAPP_RECIPIENTS`. Chaque destinataire doit avoir
   envoyé **au moins un message** au numéro WhatsApp Business au préalable
   (pour l'opt-in ; obligatoire côté Meta, quel que soit le canal).

Si vous ne voulez pas gérer de templates dans un premier temps (tests
manuels uniquement), mettez `WHATSAPP_USE_TEMPLATES=false` dans `.env` :
l'agent enverra alors du texte libre, mais **uniquement si le destinataire
vous a écrit dans les 24h précédentes**.

## Installation locale (pour tester avant de déployer)

```bash
cd whatsapp-brvm-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# éditer .env avec vos identifiants WhatsApp + Anthropic
```

## Déploiement (méthode recommandée : un seul service, h24)

Depuis cette version, `webhook_server.py` fait tout dans un seul process
qui doit rester actif en continu :
- répond aux messages WhatsApp entrants (conversationnel) ;
- abonne automatiquement tout nouveau numéro qui écrit ;
- envoie les alertes news et le recap BOC en tâche de fond (planificateur
  intégré, `brvm_agent/scheduler.py` — vérifie brvm.org toutes les
  `NEWS_POLL_INTERVAL_MINUTES`/`BOC_POLL_INTERVAL_MINUTES`, 20 min par
  défaut, et envoie dès qu'il y a du nouveau).

C'est un seul service web à déployer (ex: Render, Railway, Fly.io — un
`Procfile` est fourni : `web: uvicorn webhook_server:app --host 0.0.0.0
--port $PORT`), joignable en HTTPS, avec les variables de `.env.example`
renseignées. **Le guide détaillé, pas-à-pas, est dans
`GUIDE_DEPLOIEMENT.pdf`** (Render en exemple concret, ~10 min).

⚠️ **GitHub Actions ne convient pas** pour ce mode : pas de process
persistant possible, donc pas de webhook ni de planificateur en continu.

### Alternative : scripts + cron externe (sans conversationnel)

Si vous ne voulez que les alertes poussées (pas de réponse aux messages),
`check_news.py` et `send_recap.py` restent utilisables indépendamment,
en cron classique ou via le workflow GitHub Actions fourni
(`.github/workflows/brvm-whatsapp.yml`, secrets `WHATSAPP_TOKEN`,
`WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_RECIPIENTS`) :

```cron
*/30 8-18 * * 1-5 cd /chemin/vers/whatsapp-brvm-agent && venv/bin/python check_news.py >> agent.log 2>&1
0,15,30,45 8-18 * * 1-5 cd /chemin/vers/whatsapp-brvm-agent && venv/bin/python send_recap.py >> agent.log 2>&1
```

Dans ce mode, les destinataires viennent uniquement de `WHATSAPP_RECIPIENTS`
(pas d'auto-abonnement, puisqu'il n'y a pas de webhook pour recevoir les
messages).

## Assistant conversationnel

1. L'utilisateur envoie un message WhatsApp ("quoi de beau aujourd'hui ?").
2. Meta appelle `POST /webhook` sur le serveur.
3. Le serveur récupère les dernières données BRVM en cache (annonces +
   résumé du dernier BOC, rafraîchies au plus toutes les
   `BRVM_CONTEXT_TTL_SECONDS`, 15 min par défaut — `brvm_agent/context_cache.py`)
   et les passe en contexte à Claude (`brvm_agent/assistant.py`) avec le
   message de l'utilisateur.
4. La réponse de Claude est renvoyée sur WhatsApp en texte libre — pas
   besoin de template ici, on répond à un message reçu (fenêtre de 24h).

## Configuration (`.env`)

Voir `.env.example` pour la liste complète des variables. Les principales :

| Variable | Rôle |
|---|---|
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | Identifiants WhatsApp Cloud API (jeton **permanent** pour un usage h24) |
| `WHATSAPP_RECIPIENTS` | Numéros fixes additionnels (ex: vous-même), en plus des abonnés dynamiques |
| `WHATSAPP_USE_TEMPLATES` | `true` en production (fallback auto quand un abonné est hors fenêtre 24h) |
| `BRVM_NEWS_CATEGORIES` | Catégories d'annonces à surveiller |
| `STATE_FILE` | Fichier local de déduplication des envois |
| `SUBSCRIBERS_FILE` | Fichier local des numéros auto-abonnés |
| `ENABLE_SCHEDULER` | `true` pour que le webhook envoie aussi les alertes/recap (mode 1 service) |
| `NEWS_POLL_INTERVAL_MINUTES`, `BOC_POLL_INTERVAL_MINUTES` | Fréquence de vérification de brvm.org |
| `ANTHROPIC_API_KEY` | Clé API Claude, pour l'assistant conversationnel |
| `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET` | Sécurisation du webhook entrant |

## Limites connues

- Scraping HTML non officiel : dépend de la structure actuelle de
  `brvm.org` (vérifiée en août 2026). Un changement de mise en page côté
  BRVM peut nécessiter une mise à jour des sélecteurs.
- L'extraction des chiffres clés du BOC (`brvm_agent/boc.py`) est
  "best-effort" : si un champ n'est pas trouvé dans le PDF, il est
  simplement omis du récapitulatif plutôt que de faire échouer l'envoi.
- Les templates WhatsApp doivent être approuvés par Meta avant la mise en
  production (compter une marge de quelques heures).
- L'assistant conversationnel répond uniquement à partir du contexte BRVM
  fourni (annonces récentes + résumé du dernier BOC) : il n'a pas de mémoire
  de marché historique et peut ne pas savoir répondre à des questions très
  spécifiques (ex: cours d'une action il y a 6 mois).
- Le webhook doit rester actif en permanence, contrairement aux scripts
  `check_news.py`/`send_recap.py` qui peuvent tourner en cron ponctuel :
  prévoir un hébergement adapté (voir section dédiée).
- L'abonnement se fait uniquement par **message envoyé** au numéro
  WhatsApp Business — WhatsApp ne notifie jamais quand quelqu'un ajoute le
  numéro à son répertoire.
- Un abonné qui n'écrit jamais au bot (juste destinataire passif des
  alertes) sortira de la fenêtre de 24h : les envois automatiques
  basculeront alors sur les message templates — d'où l'intérêt de les
  faire approuver par Meta dès le lancement (voir `GUIDE_DEPLOIEMENT.pdf`).
