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
2. Récupérer `WHATSAPP_TOKEN` (jeton d'accès — utiliser un jeton permanent
   via un *System User* Meta Business pour la prod, pas le jeton temporaire
   24h de test) et `WHATSAPP_PHONE_NUMBER_ID`.
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

## Installation

```bash
cd whatsapp-brvm-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# éditer .env avec vos identifiants WhatsApp
```

## Utilisation

```bash
# Vérifier les nouvelles annonces et envoyer les alertes manquantes
python check_news.py

# Envoyer le récapitulatif du dernier BOC publié (si pas déjà envoyé)
python send_recap.py
```

### Planification (cron, exemple sur un serveur/VPS/Raspberry Pi)

```cron
# Actualités toutes les 30 min, 8h-18h, du lundi au vendredi
*/30 8-18 * * 1-5 cd /chemin/vers/whatsapp-brvm-agent && venv/bin/python check_news.py >> agent.log 2>&1

# Récapitulatif après la clôture de séance (à ajuster selon le calendrier BRVM)
0 17 * * 1-5 cd /chemin/vers/whatsapp-brvm-agent && venv/bin/python send_recap.py >> agent.log 2>&1
```

### Alternative sans serveur : GitHub Actions

Un workflow prêt à l'emploi est fourni dans
`.github/workflows/brvm-whatsapp.yml` : il tourne sur le cron GitHub Actions
sans qu'il soit nécessaire d'héberger quoi que ce soit.

1. Dans les paramètres du dépôt GitHub, ajouter les secrets `WHATSAPP_TOKEN`,
   `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_RECIPIENTS`.
2. Le workflow se déclenche automatiquement selon les crons définis, ou
   manuellement via l'onglet Actions (`workflow_dispatch`).
3. Limite à connaître : GitHub Actions ne fournit pas de disque persistant
   entre les runs. Le workflow utilise `actions/cache` pour conserver
   `state.json` (déduplication) d'un run à l'autre — fonctionnel mais moins
   robuste qu'un vrai disque persistant. Pour un usage intensif, préférer un
   petit serveur/cron dédié.

## Configuration (`.env`)

Voir `.env.example` pour la liste complète des variables. Les principales :

| Variable | Rôle |
|---|---|
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID` | Identifiants WhatsApp Cloud API |
| `WHATSAPP_RECIPIENTS` | Numéros destinataires (séparés par des virgules) |
| `WHATSAPP_USE_TEMPLATES` | `true` en production (obligatoire hors fenêtre 24h) |
| `BRVM_NEWS_CATEGORIES` | Catégories d'annonces à surveiller |
| `STATE_FILE` | Fichier local de déduplication |

## Limites connues

- Scraping HTML non officiel : dépend de la structure actuelle de
  `brvm.org` (vérifiée en août 2026). Un changement de mise en page côté
  BRVM peut nécessiter une mise à jour des sélecteurs.
- L'extraction des chiffres clés du BOC (`brvm_agent/boc.py`) est
  "best-effort" : si un champ n'est pas trouvé dans le PDF, il est
  simplement omis du récapitulatif plutôt que de faire échouer l'envoi.
- Les templates WhatsApp doivent être approuvés par Meta avant la mise en
  production (compter une marge de quelques heures).
