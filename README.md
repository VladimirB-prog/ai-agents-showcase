# Agent Travaux Publics — Démonstrateur SDK Anthropic

> **Pattern agentic loop** appliqué au domaine BTP — par un conducteur de travaux en reconversion IA.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-SDK-D4A259?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Portfolio-blueviolet)

---

## Concept

Ce projet démontre le pattern **tool use loop** du SDK Anthropic à travers une analogie
terrain : un agent IA se comporte comme un **conducteur de travaux** qui coordonne ses
sous-traitants, consigne les résultats dans un journal de chantier, et livre une synthèse finale.

Chaque concept agentique a son équivalent BTP :

| Concept IA             | Analogie BTP                              |
|------------------------|-------------------------------------------|
| Tâche utilisateur      | CCTP — Cahier des Clauses Techniques      |
| `tool_use`             | Ordre de service au sous-traitant         |
| Exécution de l'outil   | Travaux réalisés par le sous-traitant     |
| `tool_result`          | Compte-rendu remontant au CdT             |
| `end_turn`             | DOE — Dossier des Ouvrages Exécutés       |
| Journal de chantier    | Mémoire persistante de session            |

---

## La Boucle Agentique

```
┌─────────────────────────────────────────────────────────────────┐
│                       MISSION UTILISATEUR                       │
│          "Calcule le bassin, estime le réseau, synthétise"      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │   Claude (LLM)   │  ← system prompt + outils
                    │  Planification   │
                    └────────┬─────────┘
                             │
              ┌──────────────▼──────────────┐
              │      stop_reason ?          │
              └──────┬──────────────┬───────┘
                     │              │
              tool_use            end_turn
                     │              │
                     ▼              ▼
          ┌──────────────┐    ┌────────────────────┐
          │  executer_   │    │  Réponse finale    │
          │   outil()    │    │  affichée + journal│
          │  dispatcher  │    │  de chantier       │
          └──────┬───────┘    └────────────────────┘
                 │
       ┌─────────▼──────────────────────────────┐
       │           Outils disponibles           │
       │                                        │
       │  calculer_volume      → volume m³ + t  │
       │  estimer_cout_reseau  → fourchette €HT │
       │  memo_chantier        → journal session │
       └─────────┬──────────────────────────────┘
                 │
                 │  tool_result (JSON)
                 │
                 └──────────────────► Claude (LLM)
                                      ↑    (tour suivant)
                                      │
                              [boucle jusqu'à
                               end_turn ou
                               max_iterations]
```

L'historique complet (messages + tool\_results) est transmis à chaque itération :
le modèle a toujours le contexte intégral pour raisonner sur l'enchaînement des outils.

---

## Exemple de sortie terminal

```
════════════════════════════════════════════════════════════
  Agent Travaux Publics — SDK Anthropic
  Modèle : claude-sonnet-4-6
  Date   : 2026-02-19 14:32
════════════════════════════════════════════════════════════

──────────────────────────────────────────────────
  ITÉRATION 1/10
──────────────────────────────────────────────────
14:32:01 │ INFO     │ Agent démarré — Modèle : claude-sonnet-4-6
14:32:01 │ INFO     │ Mission : J'ai un chantier avec : un bassin de rétention de 60m×2...
14:32:03 │ INFO     │ Réponse — stop_reason: tool_use

  🔧 Outil demandé : calculer_volume
     Paramètres   : {"longueur_m": 60, "largeur_m": 25, "profondeur_m": 2.5, "materiau": "beton"}
     Résultat     : {"volume_m3": 3750.0, "masse_t": 9000.0, "materiau": "beton", "dimensions": "60m × 25m × 2.5m"}
14:32:03 │ INFO     │ 🔧 Outil 'calculer_volume' exécuté

──────────────────────────────────────────────────
  ITÉRATION 2/10
──────────────────────────────────────────────────
14:32:05 │ INFO     │ Réponse — stop_reason: tool_use

  🔧 Outil demandé : estimer_cout_reseau
     Paramètres   : {"type_reseau": "assainissement", "longueur_m": 350, "diametre_mm": 300}
     Résultat     : {"cout_min_ht": "85 729 €HT", "cout_max_ht": "214 323 €HT", "note": "Fourniture et pose, hors VRD"}
14:32:05 │ INFO     │ 🔧 Outil 'estimer_cout_reseau' exécuté

──────────────────────────────────────────────────
  ITÉRATION 3/10
──────────────────────────────────────────────────
14:32:07 │ INFO     │ Réponse — stop_reason: tool_use

  🔧 Outil demandé : memo_chantier
     Paramètres   : {"cle": "volume_bassin", "valeur": "3 750 m³ béton / 9 000 t"}
14:32:07 │ INFO     │ 📓 Journal chantier — 'volume_bassin' mémorisé
  🔧 Outil demandé : memo_chantier
     Paramètres   : {"cle": "cout_assainissement", "valeur": "85 729 € – 214 323 €HT (DN300, 350 ml)"}
14:32:07 │ INFO     │ 📓 Journal chantier — 'cout_assainissement' mémorisé

──────────────────────────────────────────────────
  ITÉRATION 4/10
──────────────────────────────────────────────────
14:32:09 │ INFO     │ Réponse — stop_reason: end_turn

══════════════════════════════════════════════════
  LIVRAISON FINALE DE L'AGENT
══════════════════════════════════════════════════

## Synthèse chiffrée du chantier

**Bassin de rétention 60m × 25m × 2,5m (béton)**
- Volume : 3 750 m³
- Masse béton : 9 000 tonnes

**Réseau assainissement DN300 — 350 ml**
- Coût estimatif : 85 729 € à 214 323 € HT
  (fourniture + pose, hors déviations et VRD)

**Budget global estimé : 86 K€ à 215 K€ HT**

📓 Journal de chantier :
   • volume_bassin: 3 750 m³ béton / 9 000 t
   • cout_assainissement: 85 729 € – 214 323 €HT (DN300, 350 ml)
```

4 itérations, 3 outils appelés, 0 code métier dans le prompt — le modèle orchestre seul.

---

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/VladimirB-prog/ai-agents-showcase.git
cd ai-agents-showcase

# Installer les dépendances
pip install anthropic python-dotenv

# Configurer la clé API
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

---

## Utilisation

```bash
# Mission par défaut (bassin + réseau)
python agent_travaux.py

# Mission personnalisée
python agent_travaux.py --task "Calcule le volume d'une tranchée 200m×0.8m×1.5m en terre"

# Modèle plus rapide / moins coûteux
python agent_travaux.py --model claude-haiku-4-5-20251001

# Limiter les itérations
python agent_travaux.py --max-iterations 5

# Mode silencieux (résultat final uniquement)
python agent_travaux.py --quiet
```

---

## Architecture

```
agent_travaux.py
│
├── TOOLS[]                   # Schémas JSON des outils (lus par le LLM)
│   ├── calculer_volume       # Volume + masse d'un ouvrage
│   ├── estimer_cout_reseau   # Fourchette budgétaire réseau TP
│   └── memo_chantier         # Stockage en journal de session
│
├── executer_outil()          # Dispatcher → bonne fonction Python
│
├── run_agent()               # Boucle agentique
│   ├── messages[]            # Historique complet (context window)
│   ├── stop_reason == tool_use  → executer_outil() + tool_result
│   └── stop_reason == end_turn  → affichage livraison finale
│
└── main() + argparse         # CLI utilisateur
```

### Les 3 outils (sous-traitants)

| Outil                 | Entrées                                  | Sortie                         |
|-----------------------|------------------------------------------|--------------------------------|
| `calculer_volume`     | L × l × h, matériau                     | m³, tonnes, densité            |
| `estimer_cout_reseau` | type réseau, linéaire, diamètre          | fourchette €HT (loi √diamètre) |
| `memo_chantier`       | clé, valeur                              | journal de session persistant  |

---

## Stack technique

- **Python 3.11+** — type hints systématiques, f-strings, walrus où pertinent
- **`anthropic` SDK** — messages API, tool use multi-turn, gestion des stop reasons
- **`python-dotenv`** — séparation config / code (12-factor)
- **`argparse`** — CLI sans dépendances externes
- **`logging`** structuré — timestamps, niveaux, format lisible en terminal

---

## Ce que ce projet démontre

**Pattern agentic loop** — Le modèle décide seul quels outils appeler, dans quel
ordre, combien de fois. Aucune logique de séquencement codée en dur.

**Tool use multi-turn** — Chaque `tool_result` est réinjecté dans l'historique ;
le modèle raisonne sur l'accumulation des résultats pour converger vers la livraison.

**Séparation des responsabilités** — Schémas JSON (interface LLM) vs fonctions Python
(logique métier) vs dispatcher (glue) vs boucle (orchestration). Chaque couche est
indépendante et testable.

**Domaine métier réel** — Les calculs (cubature, loi quadratique sur les diamètres,
densités matériaux) sont issus de pratiques terrain BTP, pas de placeholders.

---

## Prochaines étapes envisagées

- [ ] Tests pytest dans `tests/test_agent.py` (mock API + cas limites outils)
- [ ] Streaming sur la réponse finale (`client.messages.stream`)
- [ ] Ajout d'un outil `generer_rapport_pdf` (fpdf2)
- [ ] `pyproject.toml` + packaging propre

---

## Auteur

**Vlad** — Conducteur de travaux TP, en reconversion vers l'ingénierie IA.

Ce projet est né d'une conviction : les compétences de coordination terrain (planifier,
déléguer, synthétiser, livrer) se mappent directement sur l'architecture des agents IA.
Le SDK Anthropic est le nouveau CCTP.

---

*Construit avec le SDK Anthropic · Python 3.11 · Dunkerque, 2026*
