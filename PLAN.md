# WORK/2030 — plan de réalisation

## Architecture
React + TypeScript + Vite pour l'espace visuel, FastAPI pour les sessions et événements SSE, SQLite (WAL) pour les données et traces. Huit services logiques sont exposés par un serveur MCP local utilisant le SDK Python officiel. L'orchestrateur utilise un vrai client MCP stdio : les résultats modifient la même base que l'interface. Aucun compte externe nécessaire.

Le canvas SVG natif est retenu pour le MVP : ses objets métiers, zones et annotations sont maîtrisés et accessibles, sans dépendance à une licence de déploiement tldraw. L'automatisation enregistre des actions sémantiques internes ; ce n'est pas du Computer Use généraliste. Pas de capture d'écran ni de micro.

## Phases
1. Initialiser le dépôt et la branche `feat/work2030-mvp`.
2. Socle : données reproductibles, cinq sessions isolées, SQLite, API, serveur MCP.
3. Expériences : recherche sourcée et contexte, démonstration paramétrée, mission avec approbation et livrables.
4. Interface : espace manipulable, traces SSE, interactions visuelles et cartes à codes, console animateur.
5. Fiabilisation : tests unitaires/intégration/MCP et parcours navigateur, concurrence cinq sessions, reset et absence de clé.
6. Livraison : guides, supports imprimables, scripts, commits, PR si accès GitHub disponible.

## Arbitrages et risques
- Le mode déterministe prend en charge le scénario HORIZON et ses contraintes structurées ; il est affiché comme orchestration prédéfinie. Les intentions libres ne deviennent pas magiquement des programmes.
- Les modèles externes restent optionnels : une abstraction OpenAI/Ollama fournit un choix validé d'espace, avec limites de coût et délais ; les mutations suivent toujours la validation humaine.
- Le réseau local utilise un hôte de confiance ; protéger la console animateur par un secret et ne pas exposer le serveur sur Internet.
- Une proposition devient obsolète après toute modification de contexte ou perturbation. Revalidation côté serveur avant exécution ; restauration disponible.
- Screenpipe, OpenAdapt, UFO et tldraw sont des références d'architecture, pas du code copié. Licences et extensions détaillées dans `docs/ARCHITECTURE.md`.
