# AutoTrader — Plan de chiffrement local (modèle)

## 1) Objectifs
- Confidentialité des logs (copier, executor, system).
- Intégrité via AEAD (détection d'altération).
- Rotation & rétention conformes (7 jours).

## 2) Menaces
- Compromission de machine (accès disque).
- Fuite par sauvegarde/versionnement.
- Lecture accidentelle.

## 3) Données concernées
- Logs texte (copier/executor/system), erreurs/stack traces.

## 4) Choix crypto
- AEAD: AES-256-GCM (XChaCha20-Poly1305 en alternative).
- AAD: "AutoTraderProject" + {hostname, component, file}.
- Nonce: aléatoire, jamais réutilisé.

## 5) Hiérarchie de clés
- KEK (Key Encryption Key): protège les DEK; stocké localement dans `config/keystore/` (chiffré).
- DEK (Data Encryption Key): chiffre les logs; rotation **tous les 7 jours**.
- ID de clé: `env-YYYYMMDD`.

## 6) Rotation & rétention
- Rotation DEK: 7 jours.
- Rétention logs: 7 jours (aligné LOG_ROTATION_DAYS).
- Taille max: 20 MB → nouveau fichier.
- Compression: gzip avant chiffrement.

## 7) Stockage & permissions
- `config/keystore/`: permissions 700, non versionné.
- `.env` (plus tard sur VPS): 600.
- Logs chiffrés dans `logs/` (accès local uniquement).

## 8) Sauvegardes
- Uniquement **après chiffrement**.
- Aucun export de KEK/DEK en clair.

## 9) Incident
- Clé compromise: invalider KEK, regénérer KEK & DEK, rotation immédiate.
- Log illisible: vérifier AAD, version, nonce, intégrité; restaurer backup.

## 10) Implémentation (plus tard)
- Aucune clé réelle sur Mac.
- Génération/remplissage sur VPS (NY4) uniquement.
- Scripts de chiffrement ajoutés en phase d’implémentation (simulation d’abord).