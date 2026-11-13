# Contribuer · Contributing

**[Français](#français) · [English](#english)**

## Français

Merci de votre intérêt ! Toutes les contributions sont bienvenues, même petites : correction de faute, exemple de requête, signalement de bug.

### Idées de contributions

- Nouveaux formats d'entrée (exports Zendesk, Trustpilot, Google Avis, etc. : toujours avec des **données fictives**).
- Règles d'anonymisation pour d'autres pays (téléphones, identifiants, adresses).
- Traductions du skill et du rapport (espagnol, allemand, italien…).
- Grilles d'analyse sectorielles (banque, santé, tourisme, SaaS…) dans `skills/voix-du-client/references/`.
- Améliorations de la documentation pour les non-développeurs.

### Règles

1. **Aucune donnée réelle** : ni verbatim client, ni nom, ni e-mail réels, même anonymisés. Générez des données fictives (voir `scripts/generate_demo_data.py`).
2. **Aucun contenu protégé** : pas de copie de livres, d'articles ou de supports payants. Citez les sources avec une référence complète.
3. **Dépendances limitées** : discutez dans une *issue* avant d'en ajouter une.
4. **Code commenté et testé** : toute nouvelle fonction a au moins un test.

### Démarrer

```bash
git clone https://github.com/custovox/voc-skill.git
cd voc-skill
uv sync --extra dev
uv run pytest
```

Sur un réseau d'entreprise qui intercepte le TLS, ajoutez `UV_SYSTEM_CERTS=1`.

### Proposer une modification

1. Ouvrez une *issue* pour décrire le besoin (sauf pour les corrections évidentes).
2. Créez une branche, faites vos modifications, lancez `uv run pytest`.
3. Si vous modifiez le skill ou le plugin : `claude plugin validate .`
4. Ouvrez une *pull request* qui explique **quoi** et **pourquoi**, avec un exemple.

## English

Thanks for your interest! All contributions are welcome, even small ones: typo fixes, example prompts, bug reports.

**Ideas**: new input formats (always with **fictional data**), anonymisation rules for other countries, translations, sector-specific analysis grids, documentation for non-developers.

**Rules**: no real data (even anonymised); no copyrighted content (cite sources instead); discuss new dependencies in an issue first; comment and test new code.

**Get started**: `git clone https://github.com/custovox/voc-skill.git`, `cd voc-skill`, `uv sync --extra dev`, `uv run pytest` (add `UV_SYSTEM_CERTS=1` behind a TLS-intercepting proxy).

**Pull requests**: open an issue first for non-trivial changes, run the tests and `claude plugin validate .`, and explain what and why with an example.
