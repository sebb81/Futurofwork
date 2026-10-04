# Guide animateur — 90 minutes

Suivre `POSTES.md`, imprimer `/cartes`, ouvrir `/animateur`, saisir le code `.env`. Vérifier cinq cartes « Disponible » ; tester puis reset. Les environnements sont fictifs et identiques au départ.

| Minutes | Séquence | Manipulation | Résultat |
|---|---|---|---|
| 0–8 | Découvrir | Pilote/Copilote/Superviseur, explorer le plan et choisir une zone. | Objets métier et espace partagé. |
| 8–28 | Se souvenir | Chercher accessibilité, équipement écarté, plan calme ; ajouter/retirer une source. | Provenance, 90 cm obsolète, 140 cm et 12 places actives. |
| 28–48 | Montrer | Enregistrer l'îlot A : Fabrique, 09:00 puis 10:00. Terminer, sélectionner B et reproduire. | Deux étapes, identifiant variable, nouvelle affectation. Tester incompatibilité et annulation. |
| 48–78 | Déléguer | Préparer en démo avec accessibilité active. Refuser puis relancer/valider. Déclencher Imprévu LED. | Appels MCP, validation, mutations, livrables. Adaptation 5 700 € → 5 370 € au Pavillon. |
| 78–90 | Restituer | Exporter et comparer. | Trace et décisions humaines ; discussion sur confiance et délégation. |

À chaque transition, faire tourner les rôles par le bouton dédié. Une phrase de consigne, un essai puis discussion courte. Ni caméra ni micro nécessaires.

## Variantes

- **ACCES140** : décision sourcée. QR téléphone ou code sur le PC. Scanner ouvre le site : choisir le groupe puis ajouter la carte, sans injection silencieuse.
- **BUDGET5500** : le Pavillon à 5 700 € dépasse l'enveloppe ; la Halle à 5 200 € convient.
- **CALME12** : impose explicitement 12 places calmes.
- Retirer l'accessibilité après proposition invalide son empreinte. Sans source actualisée, l'observateur bloque la validation.
- Sélectionner LED puis Fabrique oriente son affectation dans la mission. Une incompatibilité explique son erreur.
- Alternative exclut le dernier lieu proposé. Sans candidat, l'échec est affiché : ajuster une contrainte.

## Pilotage et incidents

Pause suspend les prochaines étapes et actions humaines ; un appel en vol peut finir ou échouer avec restauration. Séquence change la navigation sans supprimer le contexte. Imprévu LED annule proprement une mission active et prépare une adaptation à valider ; si le groupe est en pause, reprendre puis Préparer côté participant.

Reset restaure le groupe ; reset global restaure les cinq après confirmation. Traces et réservations API restent. Exporter avant reset pour garder les livrables.

- Reconnexion : vérifier hôte/LAN ; SSE se reconnecte, polling complémentaire. Recharger ne supprime pas l'état.
- Proposition invalide : vérifier source active, budget, capacité, sélection zone/matériel puis relancer.
- Modèle indisponible : choisir volontairement Démo. Aucun succès silencieux.
- Échec : Diagnostic contient l'erreur ; état d'exécution restauré.
- Redémarrage : exécution interrompue après validation restaurée via snapshot. Un seul worker.
- Échec de démarrage : vérifier Python/Node, dépendances, droits sur `runtime/`, port 8000. Lire les logs réels.

Débrief : quelle source a changé la décision ? Qu'avez-vous montré plutôt que programmé ? Qu'avez-vous refusé ? Quelle supervision garder pour de vrais outils ?
