# État des fonctionnalités — MVP 0.1

## Opérationnelles

- React/TypeScript/Vite, FastAPI, SQLite WAL ; hôte LAN ou installation indépendante par poste.
- Cinq groupes avec jeu identique ; état, traces et restaurations séparés par session.
- Mémoire lexicale locale, provenance, chronologie datée, plans fictifs, versions obsolètes. Sources activables/retirables et effet visible sur contraintes.
- Canvas SVG : zones, sélection multi-ressources, glisser-déposer matériel/zone et mémoire/contexte, annotations persistées.
- Enregistrement d'affectations et horaires sur une ressource ; variable `resource_id`, reproduction de chaque étape sur d'autres objets ; contraintes et transaction atomique ; restauration.
- Client/serveur MCP Python 1.26, huit outils réellement appelés, résultats persistés, événements SSE inspectables.
- Mission HORIZON paramétrée par mémoire, budget, fréquentation, disponibilité et sélection visuelle. Lieu, plan, répartition, budget détaillé, planning, document Markdown et brouillon.
- Validation/refus serveur avant exécution ; empreinte de contexte, proposition obsolète invalidée, rollback après erreur, annulation d'une mission complète immédiatement après exécution.
- Observateur critique déterministe : capacités totale/par zone, accessibilité, mémoire absente, budget et disponibilité issus des données réelles.
- Imprévu LED : indisponibilité persistée, adaptation écran de secours et nouvelle validation. Refus, alternative et nouvelles contraintes structurées.
- Console protégée par secret : créer/vérifier les cinq sessions, progression, pause/reprise, séquences, reset individuel/global, diagnostic.
- Progression guidée sur 90 min et rotation explicite des rôles.
- Cartes physiques : vrais QR générés pour l'URL hôte, choix du groupe et ajout après clic ; alternative code court.
- Export Markdown : résultats, trace, validations ; téléchargements des documents.
- Démo sans clé et sans réseau externe après préparation.

## Partielles / bornées

- OpenAI/Ollama : conseiller de choix de lieu avec appel `select_venue` parmi les candidats vérifiés. Pipeline de coordination HORIZON. Pas de validation avec un compte fournisseur réel ou une instance Ollama dans cette livraison.
- Intention libre : texte tracé ; les contrôles structurés déterminent le scénario démo.
- Apprentissage : généralisation du seul identifiant de ressource ; pas d'apprentissage généraliste ou Computer Use.
- SVG spécialisé sans tableau blanc infini. Les zones/objets sélectionnés orientent la mission ; les traits dessinés ne sont pas interprétés.
- Services distincts logiquement, sur un serveur MCP commun, avec sous-états dans une base isolée par session.
- Objets/panels évoluent avec les actions ; pas de composition générale de l'interface par modèle.
- Pause suspend les prochains appels ; un outil en vol peut terminer ou échouer avec restauration.
- Plafond API par réservations, pas comptabilité exacte fournisseur.
- Console : état serveur, sans heartbeat prouvant la présence physique des cinq navigateurs.
- Scripts Windows fournis, non testés sur Windows depuis cet environnement Linux.

## Non réalisées

- Capture Screenpipe, mémoire vectorielle, import de données professionnelles.
- Intégrations exécutantes OpenAdapt/UFO/tldraw, contrôle du bureau, Electron.
- Agent LLM autonome avec choix libre des outils, observateur génératif.
- Webcam QR intégrée, push-to-talk et reconnaissance vocale.
- Envoi réel de messages, authentification entreprise.
- PWA sans serveur, synchronisation multi-hôtes.
