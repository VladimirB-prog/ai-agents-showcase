# 🏗️ Agent Travaux Publics — Démonstrateur SDK Anthropic

## Contexte du projet
Agent agentique Python démontrant le pattern **tool use loop** avec le SDK Anthropic.
Développé par Vlad (conducteur de travaux TP en reconversion IA) pour portfolio GitHub.

## Architecture
```
agent_travaux_src.py
├── TOOLS[]              → Schémas JSON des 3 outils (sous-traitants)
├── executer_outil()     → Dispatcher (chef de chantier)
├── run_agent()          → Boucle agentique principale
│   ├── end_turn         → Livraison finale
│   └── tool_use         → Appel sous-traitant → tool_result → loop
└── main() + argparse    → CLI utilisateur
```

## Stack technique
- Python 3.11+
- `anthropic` SDK (tool use, messages API)
- `python-dotenv` (.env pour clé API)

## Lancer le projet
```bash
pip install anthropic python-dotenv
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
python agent_travaux_src.py
python agent_travaux_src.py --task "Ta mission ici"
python agent_travaux_src.py --model claude-haiku-4-5-20251001
```

## Conventions de code
- Docstrings Google Style en français
- Type hints systématiques (Python 3.11+)
- Analogies BTP dans les commentaires
- Logging structuré avec niveaux appropriés
- Pas de valeurs hard-codées (config via CLI args ou .env)

## Ce que Claude Code peut faire ici
- Ajouter de nouveaux outils dans TOOLS[] et _TOOL_REGISTRY
- Écrire les tests pytest dans tests/test_agent.py
- Améliorer la gestion des erreurs
- Ajouter du streaming sur la réponse finale
- Générer un requirements.txt ou pyproject.toml
