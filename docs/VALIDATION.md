# Validation du MVP

Vérification locale le 4 octobre 2026, Linux, Python 3.12, Node 24 et Chromium 145.

- **26 tests pytest passés** : mémoire/provenance, suppression de contexte, actions sémantiques et batch atomique, contraintes, autorisation de mutation, persistance/isolations, budget réservé après reset, capacité réelle, parcours MCP complet, cinq missions MCP concurrentes, rollback après échec, perturbation/alternative, sélection visuelle, optimisation sous budget, binding de session MCP, validation/refus API, pause/reset/export, reprise après interruption en pause, erreurs de requête et cartes imprimables.
- **3 parcours Playwright passés** : atelier mémoire/démonstration/délégation/refus/validation/export/reset animateur ; annotation/annulation/carte physique/sélection contextuelle ; glisser-déposer mémoire et matériel. Les accès externes du navigateur sont bloqués, seul localhost est autorisé.
- **Build TypeScript/Vite passé** ; application servie par FastAPI avec assets locaux.
- **Script `start.sh` vérifié** : installation/réutilisation, génération du secret `.env`, lancement, `/api/health` (5 sessions), page participant et 15 cartes `/cartes`.
- Fournisseurs : tests de réponses contrôlées (choix d'outil valide, tool inconnu, lieu invalide et timeout). Aucun appel OpenAI facturé ni instance Ollama réelle utilisée.

Les sous-processus MCP ne fonctionnaient pas dans le bac à sable d'exécution de cet environnement ; les tests d'intégration ont été exécutés dans le même environnement hors de cette restriction. Aucun contournement n'est nécessaire sur un poste local normal.

Les dépendances actuelles émettent un avertissement de dépréciation TestClient/HTTPX et un avertissement Pydantic dans le SDK MCP. Ils ne bloquent ni les assertions ni les échanges de protocole. Windows, Firefox, Safari et l'exploitation sur le LAN physique des cinq PC restent à vérifier sur place. Les tests locaux ne constituent pas une preuve de résultat CI distant.
