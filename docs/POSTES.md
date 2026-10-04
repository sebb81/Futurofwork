# Préparer les cinq PC

1. Hôte : Python 3.11/3.12, Node 22.12+, dépôt et dépendances installés avant l'événement avec `scripts/start.sh` ou `scripts/start.ps1`.
2. `.env` : `HOST=0.0.0.0`, `PORT=8000`, secret `ANIMATOR_TOKEN` pour l'animateur. Ne distribuer aucune clé API. Mode Démo dans l'interface.
3. Autoriser TCP 8000 sur réseau privé dans le pare-feu. Même LAN sur les cinq PC ; vérifier que le Wi-Fi n'isole pas les clients. Pas d'exposition Internet.
4. Trouver l'IP hôte (`ipconfig` Windows, `ip addr` Linux). Ouvrir `http://IP-HOTE:8000`, attribuer groupes 01–05. Conserver les URLs `/g/UUID` en favoris.
5. Générer les QR LAN : `.venv/bin/python scripts/cards.py --base-url http://IP-HOTE:8000` (Windows : `.venv/Scripts/python.exe`). Ouvrir `/cartes`, imprimer 15 cartes A4. Les QR par défaut localhost doivent être régénérés.
6. Navigateur récent, 1440×900 conseillé ; interface réactive. F11/bouton plein écran ; zoom navigateur pour projection selon distance.
7. Console animateur, essai puis reset global. Aucun compte ou micro nécessaire.

## Sans Internet

Après dépendances/build, le mode Démo n'utilise aucun réseau externe. Le script Bash réutilise dépendances et build à jour. Windows : `scripts/run-local.ps1` après préparation.

Avant atelier, couper Internet en gardant LAN actif, recharger les postes et exécuter la mission. Le serveur hôte reste nécessaire. Installation indépendante possible sur chaque PC : localhost et base propre (cinq groupes locaux). La console centrale ne pilote alors pas les autres installations.

## Sauvegarde et purge

Exporter avant reset. L'état survit au navigateur et au redémarrage. Reset conserve traces/réservations. Purge complète : arrêter le serveur et supprimer uniquement `runtime/work2030.sqlite`, `-wal`, `-shm` ; le prochain lancement crée de nouveaux UUID, donc renouveler les favoris.

Ne pas copier une SQLite active avec WAL : arrêter avant sauvegarde ou utiliser l'API backup SQLite. `/api/health` doit répondre `status: ok`, `sessions: 5`. Tester recherche/affectation depuis chacun des cinq PC : la console ne prouve pas leur présence physique.
