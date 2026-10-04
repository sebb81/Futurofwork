# WORK/2030 — CRTHON 10

Un environnement expérimental pour cinq trinômes : retrouver une mémoire sourcée, démontrer une manipulation, puis coordonner huit outils MCP pour préparer l'événement fictif HORIZON.

**Le MVP fonctionne sans clé API.** Le mode par défaut est une orchestration prédéfinie, affichée comme telle. Ses appels MCP, affectations, calculs, documents et brouillons modifient réellement SQLite. Aucun écran ou micro n'est enregistré.

## Lancer

Prérequis : Python **3.11–3.12**, Node **22.12+**, npm et un navigateur récent. L'installation initiale télécharge les dépendances ; l'atelier démo n'a ensuite besoin que du réseau local.

```bash
git clone https://github.com/sebb81/Futurofwork.git
cd Futurofwork
git switch feat/work2030-mvp
./scripts/start.sh
```

Windows PowerShell : `powershell -ExecutionPolicy Bypass -File scripts/start.ps1`. Après installation, `scripts/run-local.ps1` lance sans réinstaller.

Ouvrir **http://localhost:8000**, choisir un trinôme. Les cinq sessions sont créées automatiquement au démarrage. Console animateur : **http://localhost:8000/animateur**. Le script crée `.env` avec un code animateur aléatoire ; lire `ANIMATOR_TOKEN` dans ce fichier. En lancement manuel sans `.env`, le code de développement est `work2030-local` : le remplacer pour le réseau local.

L'hôte sert les cinq PC à `http://IP-HOTE:8000`. Un seul processus Uvicorn gère l'atelier ; ne pas utiliser plusieurs workers. F11 ou le bouton plein écran ouvre l'expérience sur tout l'écran. Les icônes, styles et polices système sont locaux.

## Un parcours complet en cinq minutes

1. « Se souvenir » : chercher **accessibilité**, ajouter **Décision accessibilité confirmée** au contexte. Le cheminement requis passe de 90 à 140 cm. Retirer puis réajouter pour comparer.
2. « Montrer » : **Enregistrer**, sélectionner **Îlot découverte A**, zone **Fabrique**, affecter à 09:00–12:00 puis modifier à 10:00–12:00. **J'ai terminé**, désélectionner A, sélectionner B puis **Fais-le pour moi**. Les deux étapes sont rejouées sur B. L'annulation du plan restaure l'état précédent.
3. « Déléguer » : conserver **Démo**, **Préparer la mission**. Plusieurs appels MCP apparaissent. Aucun livrable n'est encore exécuté ; l'observateur relève les problèmes réels.
4. **Refuser** laisse les données métier inchangées. Relancer puis **Valider** crée plan, planning, document et brouillon local. Une proposition devient obsolète si le contexte change : relancer.
5. Console animateur : **Imprévu LED** rend le matériel indisponible et prépare une adaptation à valider. **Pause**, séquence et **Reset** agissent sur le groupe choisi. « Restituer » exporte les résultats et la trace Markdown.

Le texte libre est conservé dans l'intention et la trace. **En démo, il ne modifie pas les règles du scénario** : utiliser les contrôles de contraintes, cartes physiques, contexte et sélection de ressources/zone. L'annotation libre est persistée, mais n'est pas interprétée par une IA visuelle.

## Développement et vérification

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
cd frontend
npm ci
npm run build
cd ..
.venv/bin/pytest -q
```

Tests navigateur : `cd frontend`, `npx playwright install chromium`, `npm run test:e2e`. Playwright démarre un serveur isolé sur 8100. La CI exécute backend, build et Chromium.

Rechargement en développement : `.venv/bin/uvicorn work2030.api:app --reload --port 8000`, puis `cd frontend && npm run dev` dans un second terminal. Interface sur 5173, proxy `/api` vers FastAPI.

## MCP et modèles optionnels

Serveur MCP stdio : `.venv/bin/python -m work2030.mcp_server`. Outils : `Memory`, `Resources`, `Space`, `Calendar`, `Budget`, `Documents`, `Messaging`, `Workspace`. Chaque appel reçoit `session_id` et `args` ; chaque sous-processus de l'orchestrateur est lié à un groupe. Aucun outil ne contrôle l'ordinateur hôte.

OpenAI : renseigner `OPENAI_API_KEY` et `MODEL_NAME` côté serveur dans `.env`, choisir OpenAI dans l'interface. Ollama : renseigner `OLLAMA_URL`, un modèle avec tool calling (`MODEL_NAME=qwen3:8b` par exemple), choisir Ollama. **Ces intégrations fournissent un conseiller de choix de lieu, pas un agent généraliste.** Le modèle appelle `select_venue` parmi les lieux admissibles ; le pipeline reste borné et vérifié. Les appels externes réels ne sont pas certifiés avec un compte fournisseur dans cette livraison.

Timeout configurable, sortie maximale 400 tokens, budget de **réservation** par session. `API_SESSION_BUDGET_USD` et `API_CALL_RESERVATION_USD` bloquent les nouveaux appels une fois l'enveloppe réservée atteinte. Ce compteur n'est pas la facture fournisseur : choisir une réservation au moins égale au coût maximal du modèle configuré et régler aussi son plafond fournisseur. Reset et annulation ne remboursent pas les réservations. Aucun échec modèle n'est transformé silencieusement en succès démo.

## Livraison et limites

- [État précis des fonctionnalités](docs/FEATURES.md)
- [Guide animateur](docs/ANIMATEUR.md)
- [Préparer les cinq PC et le LAN](docs/POSTES.md)
- [Architecture et licences vérifiées](docs/ARCHITECTURE.md)
- [Cartes imprimables QR et codes courts](docs/cards.html) — également `/cartes`
- [Plan de réalisation](PLAN.md)

L'accueil permet volontairement de choisir n'importe quel groupe : l'isolation des données n'est pas une authentification entre participants. Tout est fictif et destiné à un LAN de confiance, sans exposition Internet. Base et traces sont dans `runtime/`, ignoré par Git. Les traces survivent aux resets ; arrêter le serveur et supprimer sa base fictive permet une purge complète.
