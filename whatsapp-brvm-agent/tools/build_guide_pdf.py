# -*- coding: utf-8 -*-
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    ListFlowable, ListItem, HRFlowable, KeepTogether,
)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "GUIDE_DEPLOIEMENT.pdf")

# ---------- Styles ----------
styles = getSampleStyleSheet()

NAVY = colors.HexColor("#12213b")
BLUE = colors.HexColor("#1f5aa8")
GREEN = colors.HexColor("#1f7a4d")
GREY = colors.HexColor("#5a6472")
LIGHT_BG = colors.HexColor("#eef2f8")
WARN_BG = colors.HexColor("#fdf1e0")
WARN_BORDER = colors.HexColor("#c97a1a")
CODE_BG = colors.HexColor("#f4f4f4")

styles.add(ParagraphStyle(
    name="CoverTitle", fontName="Helvetica-Bold", fontSize=26, leading=32,
    textColor=NAVY, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="CoverSubtitle", fontName="Helvetica", fontSize=13, leading=18,
    textColor=GREY, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="H1", fontName="Helvetica-Bold", fontSize=17, leading=21,
    textColor=NAVY, spaceBefore=6, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="H2", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
    textColor=BLUE, spaceBefore=14, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Body", fontName="Helvetica", fontSize=10, leading=14.5,
    textColor=colors.HexColor("#1a1a1a"), spaceAfter=6, alignment=TA_LEFT,
))
styles.add(ParagraphStyle(
    name="BodyBold", parent=styles["Body"], fontName="Helvetica-Bold",
))
styles.add(ParagraphStyle(
    name="MyBullet", parent=styles["Body"], leftIndent=10, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="CodeBlock", fontName="Courier", fontSize=9, leading=12.5,
    textColor=colors.HexColor("#20232a"), backColor=CODE_BG,
    borderPadding=(6, 8, 6, 8), spaceAfter=8, spaceBefore=2,
))
styles.add(ParagraphStyle(
    name="Small", parent=styles["Body"], fontSize=8.5, textColor=GREY,
))
styles.add(ParagraphStyle(
    name="StepTitle", fontName="Helvetica-Bold", fontSize=11.5, leading=15,
    textColor=colors.white,
))

def para(text, style="Body"):
    return Paragraph(text, styles[style])


def h1(text):
    return [para(text, "H1"), HRFlowable(width="100%", thickness=1.2, color=BLUE, spaceAfter=10)]


def h2(text):
    return para(text, "H2")


def code_block(text):
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    escaped = escaped.replace("\n", "<br/>")
    return Paragraph(escaped, styles["CodeBlock"])


def bullets(items):
    return ListFlowable(
        [ListItem(para(i, "MyBullet"), leftIndent=8) for i in items],
        bulletType="bullet", start="•", leftIndent=14, spaceBefore=2, spaceAfter=8,
    )


def numbered(items):
    return ListFlowable(
        [ListItem(para(i, "Body"), leftIndent=8) for i in items],
        bulletType="1", leftIndent=18, spaceBefore=2, spaceAfter=10,
    )


def callout(title, text, kind="warn"):
    bg = WARN_BG if kind == "warn" else LIGHT_BG
    border = WARN_BORDER if kind == "warn" else BLUE
    icon = "⚠" if kind == "warn" else "ℹ"
    t = Table(
        [[para(f"<b>{icon} {title}</b><br/>{text}", "Body")]],
        colWidths=[16.2 * cm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 1, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def step_header(number, title, minutes):
    t = Table(
        [[para(f"ÉTAPE {number}", "StepTitle"), para(title, "StepTitle"), para(f"~{minutes}", "StepTitle")]],
        colWidths=[2.6 * cm, 11.2 * cm, 2.4 * cm],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("RIGHTPADDING", (2, 0), (2, 0), 10),
    ]))
    return t


story = []

# ---------- Cover ----------
story.append(Spacer(1, 5 * cm))
story.append(para("Agent WhatsApp BRVM", "CoverTitle"))
story.append(para("Guide de déploiement — de zéro à un agent qui tourne h24", "CoverSubtitle"))
story.append(Spacer(1, 0.4 * cm))
story.append(para("Alertes news automatiques · Récap + BOC en fin de séance · Assistant conversationnel Claude", "CoverSubtitle"))
story.append(Spacer(1, 1.5 * cm))
story.append(HRFlowable(width="60%", thickness=1, color=BLUE))
story.append(Spacer(1, 0.6 * cm))
story.append(para(
    "Ce guide s'adresse à deux publics :", "Body"))
story.append(bullets([
    "<b>Vous (l'administrateur)</b> : déployer l'agent — environ 10 minutes de manipulation active "
    "(certaines étapes, comme la validation d'un template par Meta, se terminent en tâche de fond).",
    "<b>Une connaissance qui veut recevoir les alertes</b> : s'abonner — moins de 5 minutes, "
    "un seul message WhatsApp à envoyer (voir la dernière section, à leur transférer telle quelle).",
]))
story.append(Spacer(1, 1 * cm))
story.append(para(
    "Repo du projet : dossier <font face='Courier'>whatsapp-brvm-agent/</font> — "
    "branche <font face='Courier'>claude/whatsapp-brvm-news-agent-icafwf</font>.",
    "Small",
))
story.append(PageBreak())

# ---------- Vue d'ensemble ----------
story += h1("Vue d'ensemble")
story.append(para(
    "Un seul service tourne en continu et fait tout à la fois :", "Body"))
story.append(bullets([
    "il répond à tout message WhatsApp reçu (assistant conversationnel, propulsé par Claude) ;",
    "il abonne automatiquement toute personne qui lui écrit pour la première fois ;",
    "il vérifie brvm.org toutes les 20 minutes et pousse une alerte à chaque nouvelle annonce ;",
    "il détecte la publication du Bulletin Officiel de la Cote (BOC) en fin de séance et l'envoie "
    "(résumé chiffré + PDF officiel) à tous les abonnés.",
]))
story.append(callout(
    "Point essentiel à comprendre avant de commencer",
    "WhatsApp ne prévient <b>jamais</b> une entreprise quand quelqu'un l'ajoute à ses contacts. "
    "Le seul évènement qui compte, c'est un <b>message envoyé</b> au numéro. C'est pour ça que "
    "l'abonnement se fait par un premier message (voir la section « Faire s'abonner quelqu'un »), "
    "et pas par un simple ajout au répertoire.",
))
story.append(Spacer(1, 0.3 * cm))
story.append(para(
    "Ce que vous allez créer, dans l'ordre : un compte développeur Meta (gratuit) → une clé API "
    "Claude (Anthropic) → un déploiement du code sur Render (hébergeur, ~7$/mois pour un "
    "fonctionnement réellement h24) → la connexion entre les deux.", "Body"))
story.append(PageBreak())

# ---------- Avant de commencer ----------
story += h1("Avant de commencer")
story.append(para("Une check-list de ce qu'il vous faut sous la main :", "Body"))
story.append(bullets([
    "Un numéro de téléphone <b>dédié</b> à WhatsApp Business (pas votre numéro perso habituel — "
    "une fois lié à l'API Cloud, il ne peut plus servir sur l'appli WhatsApp classique).",
    "Un compte Facebook (nécessaire pour créer un compte développeur Meta).",
    "Une carte bancaire, pour l'hébergement (~7$/mois) — il existe une option gratuite mais moins "
    "fiable pour un usage h24, voir l'encart en fin de guide.",
    "Un compte GitHub (vous en avez déjà un, le code y est déjà poussé sur la branche indiquée en couverture).",
]))
story.append(Spacer(1, 0.2 * cm))
story.append(para("Temps total : 10-15 minutes de manipulation active. Deux choses finissent "
                   "en tâche de fond après coup (peuvent prendre de quelques minutes à quelques "
                   "heures) : la validation des message templates par Meta, et le premier "
                   "déploiement sur Render.", "Body"))
story.append(PageBreak())

# ---------- ETAPE 1 ----------
story.append(step_header("1", "Créer l'app Meta + le numéro WhatsApp Business", "5 min"))
story.append(Spacer(1, 0.3 * cm))
story.append(numbered([
    "Allez sur developers.facebook.com/apps → <b>Créer une application</b> → type <b>Business</b>.",
    "Dans le tableau de bord de l'app, ajoutez le produit <b>WhatsApp</b>.",
    "Meta crée automatiquement un <b>numéro de test</b> gratuit — suffisant pour tout ce guide, y "
    "compris la mise en production. Vous pourrez migrer vers votre propre numéro plus tard "
    "depuis le même endroit si besoin.",
    "Dans l'onglet <b>WhatsApp → Configuration de l'API</b>, notez le <b>Phone number ID</b> "
    "(= <font face='Courier'>WHATSAPP_PHONE_NUMBER_ID</font>).",
]))
story.append(callout(
    "Jeton d'accès : prenez le permanent, pas le temporaire",
    "La page affiche par défaut un jeton « temporaire » qui expire au bout de 24h — "
    "l'agent s'arrêterait de fonctionner le lendemain. Pour un jeton permanent : "
    "<b>Meta Business Suite → Paramètres de l'entreprise → Utilisateurs → Utilisateurs système</b> "
    "→ <b>Ajouter</b> (rôle Admin) → sur l'utilisateur créé, <b>Générer un nouveau jeton</b> → "
    "sélectionnez votre app, cochez la permission <font face='Courier'>whatsapp_business_messaging</font> "
    "(et <font face='Courier'>whatsapp_business_management</font>) → expiration <b>Jamais</b>. "
    "Copiez ce jeton (= <font face='Courier'>WHATSAPP_TOKEN</font>), il ne sera plus jamais réaffiché.",
))
story.append(Spacer(1, 0.3 * cm))
story.append(para(
    "Notez aussi, dans <b>Paramètres de l'app → De base</b>, l'<b>App secret</b> "
    "(= <font face='Courier'>WHATSAPP_APP_SECRET</font>) : il sert à vérifier que les messages "
    "reçus proviennent bien de Meta.", "Body"))
story.append(PageBreak())

# ---------- ETAPE 2 ----------
story.append(step_header("2", "Créer la clé API Claude", "1 min"))
story.append(Spacer(1, 0.3 * cm))
story.append(numbered([
    "Allez sur console.anthropic.com → <b>API Keys</b> → <b>Create Key</b>.",
    "Copiez la clé générée (= <font face='Courier'>ANTHROPIC_API_KEY</font>), elle ne sera "
    "affichée qu'une fois.",
]))
story.append(Spacer(1, 0.5 * cm))
story.append(h2("Ce que vous devez avoir en main à ce stade"))
data = [
    ["Variable", "Où la trouver"],
    ["WHATSAPP_TOKEN", "Utilisateur système Meta → jeton permanent"],
    ["WHATSAPP_PHONE_NUMBER_ID", "WhatsApp → Configuration de l'API"],
    ["WHATSAPP_APP_SECRET", "Paramètres de l'app → De base"],
    ["ANTHROPIC_API_KEY", "console.anthropic.com → API Keys"],
]
tbl = Table(data, colWidths=[6.2 * cm, 9.6 * cm])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (0, -1), "Courier"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d2e0")),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
]))
story.append(tbl)
story.append(PageBreak())

# ---------- ETAPE 3 ----------
story.append(step_header("3", "Déployer le code sur Render (h24)", "5 min"))
story.append(Spacer(1, 0.3 * cm))
story.append(para(
    "Render est le plus simple pour démarrer : vous connectez le dépôt GitHub, vous collez "
    "les variables, c'est tout — pas de ligne de commande. Le plan <b>Starter</b> (~7$/mois) "
    "ne met pas le service en veille, ce qui est indispensable pour un fonctionnement h24 "
    "(voir l'encart en fin de guide pour l'option gratuite).", "Body"))
story.append(numbered([
    "Sur render.com, créez un compte (connexion via GitHub recommandée).",
    "<b>New</b> → <b>Web Service</b> → sélectionnez le dépôt "
    "<font face='Courier'>Formation_GIT</font> → branche "
    "<font face='Courier'>claude/whatsapp-brvm-news-agent-icafwf</font>.",
    "<b>Root Directory</b> : <font face='Courier'>whatsapp-brvm-agent</font>",
    "<b>Runtime</b> : Python 3",
    "<b>Build Command</b> : <font face='Courier'>pip install -r requirements.txt</font>",
    "<b>Start Command</b> : "
    "<font face='Courier'>uvicorn webhook_server:app --host 0.0.0.0 --port $PORT</font>",
    "<b>Instance Type</b> : Starter (le plan gratuit se met en veille après inactivité, "
    "incompatible avec un fonctionnement h24).",
    "Dans <b>Environment Variables</b>, ajoutez les variables ci-dessous, puis <b>Create Web Service</b>.",
]))
env_data = [
    ["Variable", "Valeur"],
    ["WHATSAPP_TOKEN", "(le jeton permanent de l'étape 1)"],
    ["WHATSAPP_PHONE_NUMBER_ID", "(de l'étape 1)"],
    ["WHATSAPP_APP_SECRET", "(de l'étape 1)"],
    ["ANTHROPIC_API_KEY", "(de l'étape 2)"],
    ["WHATSAPP_VERIFY_TOKEN", "une phrase que vous inventez, ex: brvm-secret-2026"],
    ["ENABLE_SCHEDULER", "true"],
]
tbl2 = Table(env_data, colWidths=[6.2 * cm, 9.6 * cm])
tbl2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (0, -1), "Courier"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.7),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d2e0")),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
]))
story.append(tbl2)
story.append(Spacer(1, 0.3 * cm))
story.append(para(
    "Le déploiement prend 2-3 minutes. Une fois terminé, Render affiche l'URL du service "
    "(ex: <font face='Courier'>https://brvm-agent.onrender.com</font>) — notez-la, "
    "vous en avez besoin à l'étape suivante.", "Body"))
story.append(PageBreak())

# ---------- ETAPE 4 ----------
story.append(step_header("4", "Connecter le webhook côté Meta", "2 min"))
story.append(Spacer(1, 0.3 * cm))
story.append(numbered([
    "Dans le dashboard de l'app Meta → <b>WhatsApp → Configuration</b>.",
    "Champ <b>Callback URL</b> : votre URL Render + <font face='Courier'>/webhook</font> "
    "(ex: <font face='Courier'>https://brvm-agent.onrender.com/webhook</font>).",
    "Champ <b>Verify token</b> : exactement la même valeur que "
    "<font face='Courier'>WHATSAPP_VERIFY_TOKEN</font> saisie sur Render à l'étape précédente.",
    "Cliquez <b>Vérifier et enregistrer</b> — Meta appelle votre service pour valider "
    "(ça doit passer au vert immédiatement si l'étape 3 est bien terminée).",
    "Juste en dessous, dans <b>Webhook fields</b>, abonnez-vous au champ "
    "<font face='Courier'>messages</font>.",
]))
story.append(callout(
    "Ça ne marche pas ?",
    "Vérifiez que le service Render est bien « Live » (onglet Logs), que "
    "<font face='Courier'>WHATSAPP_VERIFY_TOKEN</font> est identique des deux côtés (attention "
    "aux espaces), et que l'URL se termine bien par <font face='Courier'>/webhook</font>.",
))
story.append(PageBreak())

# ---------- ETAPE 5 ----------
story.append(step_header("5", "Créer les 2 templates de secours", "3 min + attente Meta"))
story.append(Spacer(1, 0.3 * cm))
story.append(para(
    "Cette étape n'empêche pas de tester tout de suite (étape 6) — mais faites-la dès "
    "maintenant, car Meta met de quelques minutes à quelques heures pour valider. Sans template "
    "approuvé, un abonné qui n'écrit jamais au bot finira, après 24h, par ne plus recevoir "
    "les alertes automatiques (contrainte WhatsApp, pas modifiable). Avec le template, l'agent "
    "bascule dessus automatiquement dans ce cas — vous n'avez rien à faire de plus une fois "
    "les templates approuvés.", "Body"))
story.append(numbered([
    "Meta Business Suite → <b>WhatsApp Manager → Modèles de message → Créer un modèle</b>.",
    "Catégorie : <b>Utility</b>. Nom : <font face='Courier'>brvm_news_alert</font>. Langue : Français.",
    "Corps du message :",
]))
story.append(code_block(
    "\U0001F4C8 BRVM - Nouvelle annonce\n"
    "Société : {{1}}\n"
    "{{2}}\n"
    "\U0001F517 {{3}}"
))
story.append(numbered([
    "Soumettez. Recommencez avec un 2e template, nom "
    "<font face='Courier'>brvm_boc_recap</font>, catégorie Utility, langue Français, "
    "en-tête <b>Document</b> (dynamique), corps :",
]))
story.append(code_block(
    "\U0001F4CA {{1}}\n"
    "BRVM Composite : {{2}}\n"
    "BRVM 30 : {{3}}\n"
    "Le bulletin officiel complet est joint à ce message."
))
story.append(para(
    "Les noms doivent correspondre exactement à "
    "<font face='Courier'>WHATSAPP_NEWS_TEMPLATE_NAME</font> / "
    "<font face='Courier'>WHATSAPP_RECAP_TEMPLATE_NAME</font> (valeurs par défaut, rien à "
    "changer si vous gardez ces noms).", "Body"))
story.append(PageBreak())

# ---------- ETAPE 6 ----------
story.append(step_header("6", "Tester (10 minutes chrono)", "10 min"))
story.append(Spacer(1, 0.3 * cm))
story.append(para("Depuis votre propre WhatsApp :", "Body"))
story.append(numbered([
    "Trouvez le numéro de test dans Meta → WhatsApp → Configuration de l'API (section « To »).",
    "Ajoutez d'abord votre numéro à la liste des destinataires autorisés du numéro de test "
    "(bouton <b>Manage phone number list</b>) — obligatoire uniquement pour le numéro de test "
    "gratuit, pas pour un vrai numéro Business.",
    "Envoyez n'importe quel message à ce numéro depuis WhatsApp (ex: « Salut »).",
    "Vous devez recevoir <b>2 messages</b> en retour : un message de bienvenue "
    "(confirmant l'abonnement automatique), puis une réponse conversationnelle générée par "
    "Claude.",
    "Renvoyez un message, ex: « quoi de beau aujourd'hui sur la BRVM ? » → une réponse "
    "contextualisée doit arriver en quelques secondes.",
    "Écrivez <font face='Courier'>STOP</font> → confirmation de désabonnement. Écrivez de "
    "nouveau n'importe quoi → réabonnement automatique.",
]))
story.append(para(
    "Les alertes news et le recap BOC se déclenchent automatiquement dès qu'il y a du nouveau "
    "sur brvm.org (vérification toutes les 20 min) — pas besoin de les provoquer pour valider "
    "que le mécanisme d'abonnement et le conversationnel fonctionnent, ce sont les points 3 à 6 "
    "ci-dessus qui le prouvent.", "Body"))
story.append(PageBreak())

# ---------- Faire s'abonner quelqu'un ----------
story += h1("Faire s'abonner une connaissance (< 5 minutes, à transférer)")
story.append(para(
    "Le texte ci-dessous est prêt à copier-coller et envoyer tel quel à quelqu'un — "
    "il explique en 2 lignes comment s'abonner.", "Body"))
story.append(Spacer(1, 0.2 * cm))
story.append(code_block(
    "Salut ! Pour recevoir les actus BRVM (annonces + recap de fin de séance) et pouvoir "
    "poser des questions sur la bourse directement sur WhatsApp, clique ici et appuie sur "
    "Envoyer :\n"
    "https://wa.me/<VOTRE_NUMERO>?text=Bonjour"
))
story.append(para(
    "Remplacez <font face='Courier'>&lt;VOTRE_NUMERO&gt;</font> par le numéro WhatsApp Business "
    "au format international sans le « + » (ex: 2250700000000). Le lien ouvre "
    "directement WhatsApp avec le message pré-rempli : la personne n'a plus qu'à appuyer sur "
    "Envoyer. C'est ce clic qui déclenche l'abonnement automatique et le message de bienvenue.",
    "Body"))
story.append(callout(
    "Pourquoi pas juste « ajoute ce contact » ?",
    "Parce que ça ne suffit pas : WhatsApp ne prévient jamais l'agent quand quelqu'un l'ajoute "
    "à son répertoire. Il faut un message envoyé, d'où le lien pré-rempli — le geste le plus "
    "simple possible pour arriver au même résultat en un seul tap.",
    kind="info",
))
story.append(PageBreak())

# ---------- FAQ / Limites ----------
story += h1("À savoir avant de partager largement")
story.append(bullets([
    "<b>Numéro de test Meta</b> : limité à des destinataires explicitement autorisés et à un "
    "volume modéré de messages par jour. Pour un vrai lancement public, associez votre propre "
    "numéro WhatsApp Business (même écran Meta que l'étape 1, bouton « Add phone number ») — "
    "aucune autre variable à changer.",
    "<b>Fenêtre de 24h</b> : un abonné qui n'écrit jamais au bot sortira de la fenêtre de 24h "
    "entre deux messages actifs de sa part ; l'agent bascule alors automatiquement sur les "
    "templates de l'étape 5. Sans template approuvé, ce message-là serait perdu (mais pas les "
    "suivants une fois le template validé).",
    "<b>Scraping brvm.org</b> : le site n'a pas d'API officielle ; si sa mise en page change, "
    "certains champs peuvent devenir vides le temps d'ajuster le code — jamais de plantage "
    "complet, l'agent est conçu pour dégrader proprement.",
    "<b>Coût</b> : hébergement Render Starter (~7$/mois) + usage API Claude (quelques centimes "
    "par conversation) + WhatsApp Cloud API (gratuit jusqu'à un certain volume mensuel de "
    "conversations, au-delà tarification Meta standard).",
]))
story.append(Spacer(1, 0.3 * cm))
story.append(h2("Alternative gratuite (moins fiable pour du h24)"))
story.append(para(
    "Render propose un plan gratuit, mais il met le service en veille après 15 minutes "
    "d'inactivité : le webhook rate des messages entrants pendant la veille, et le "
    "planificateur d'alertes ne tourne pas non plus pendant ce temps. Fly.io propose un usage "
    "gratuit réellement toujours actif pour un petit service comme celui-ci, mais demande "
    "d'installer leur outil en ligne de commande (<font face='Courier'>flyctl</font>) — un peu "
    "moins « clic-clic » que Render. À réserver à qui est déjà à l'aise avec un "
    "terminal.", "Body"))
story.append(Spacer(1, 0.6 * cm))
story.append(HRFlowable(width="100%", thickness=0.7, color=GREY))
story.append(Spacer(1, 0.2 * cm))
story.append(para(
    "Documentation complète et code source : dossier <font face='Courier'>whatsapp-brvm-agent/</font> "
    "du dépôt, fichier <font face='Courier'>README.md</font>.", "Small"))


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#c9d2e0"))
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.4 * cm, 19 * cm, 1.4 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.0 * cm, "Agent WhatsApp BRVM — Guide de déploiement")
    canvas.drawRightString(19 * cm, 1.0 * cm, f"Page {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2.2 * cm,
    title="Agent WhatsApp BRVM - Guide de deploiement",
    author="Agent WhatsApp BRVM",
)
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print("PDF genere:", OUT)
