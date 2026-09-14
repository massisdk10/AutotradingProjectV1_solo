# AutoTrader Project — Structure Notes

## 1) Root level
- `.env.template` → modèle d’environnement
- `.gitignore` → protection des fichiers sensibles
- `/config/` → paramètres du projet et fichiers de chiffrement
- `/copier/` → logique du copieur Telegram
- `/executor/` → exécution MT5
- `/logs/` → stockage chiffré des journaux
- `/docs/` → documentation interne
- `/tests/` → scénarios de test et simulations

## 2) Security guidelines
- Ne jamais stocker de vraies clés dans `.env.template` ou `config/`
- Les fichiers dans `/logs/` sont chiffrés, rotation 7 jours
- `config/keystore/` contient les clés de chiffrement locales (non versionné)