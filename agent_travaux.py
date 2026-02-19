#!/usr/bin/env python3
"""
Agent Agentique TP — Démonstrateur SDK Anthropic

Analogie BTP : Ce script est un conducteur de travaux IA.
Il reçoit une mission (prompt utilisateur), dispose d'outils
(calculer, analyser, mémoriser), et boucle jusqu'à livraison.

C'est exactement comme un CdT qui lit le CCTP, appelle ses sous-traitants
(tools), lit leurs réponses, et continue jusqu'à remettre le DOE.

Architecture : Agentic Loop = CCTP → Plan d'exécution → Appels sous-traitants → Livraison

Usage:
    python agent_travaux_src.py
    python agent_travaux_src.py --task "Calcule le volume d'un bassin de 50x20x3m"
    python agent_travaux_src.py --model claude-haiku-4-5-20251001 --max-iterations 5

Requirements:
    pip install anthropic python-dotenv

Author: Vlad / SRC Dunkerque
Date: 2026-02-19
Python: 3.11+
"""

import argparse
import json
import logging
import math
import os
import sys
from datetime import datetime
from typing import Any

import anthropic
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# CONFIGURATION LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CHARGEMENT .ENV
# ─────────────────────────────────────────────
load_dotenv()  # Charge ANTHROPIC_API_KEY depuis .env si présent


# ═══════════════════════════════════════════════════════════════
# DÉFINITION DES OUTILS (les "sous-traitants" de l'agent)
# ═══════════════════════════════════════════════════════════════

# Schéma JSON des outils — le modèle les lit pour savoir quoi appeler
TOOLS: list[dict] = [
    {
        "name": "calculer_volume",
        "description": (
            "Calcule le volume d'une excavation ou d'un ouvrage TP. "
            "Analogie : la topographie du chantier. "
            "Retourne le volume en m³ et la masse estimée en tonnes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "longueur_m": {"type": "number", "description": "Longueur en mètres"},
                "largeur_m":  {"type": "number", "description": "Largeur en mètres"},
                "profondeur_m": {"type": "number", "description": "Profondeur/hauteur en mètres"},
                "materiau": {
                    "type": "string",
                    "description": "Type de matériau : terre, beton, eau, gravier",
                    "enum": ["terre", "beton", "eau", "gravier"],
                    "default": "terre",
                },
            },
            "required": ["longueur_m", "largeur_m", "profondeur_m"],
        },
    },
    {
        "name": "estimer_cout_reseau",
        "description": (
            "Estime le coût d'un réseau TP (eau potable, assainissement, pluvial). "
            "Analogie : le devis du sous-traitant canalisateur. "
            "Retourne une fourchette de coût en euros HT."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "type_reseau": {
                    "type": "string",
                    "description": "Nature du réseau",
                    "enum": ["eau_potable", "assainissement", "pluvial", "telecom"],
                },
                "longueur_m": {"type": "number", "description": "Linéaire en mètres"},
                "diametre_mm": {"type": "number", "description": "Diamètre de canalisation en mm"},
            },
            "required": ["type_reseau", "longueur_m"],
        },
    },
    {
        "name": "memo_chantier",
        "description": (
            "Mémorise une information clé dans le journal de chantier de la session. "
            "Analogie : le journal de chantier papier du CdT. "
            "Utile pour stocker des résultats intermédiaires à réutiliser."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cle":    {"type": "string", "description": "Identifiant de la note (ex: 'volume_bassin')"},
                "valeur": {"type": "string", "description": "Valeur ou texte à mémoriser"},
            },
            "required": ["cle", "valeur"],
        },
    },
]


# ═══════════════════════════════════════════════════════════════
# IMPLÉMENTATION DES OUTILS
# Analogie BTP : les sous-traitants spécialisés qui exécutent
# ═══════════════════════════════════════════════════════════════

# Journal de chantier partagé pour la session (mémoire de l'agent)
_journal_chantier: dict[str, str] = {}

# Densités par matériau (t/m³)
_DENSITES: dict[str, float] = {
    "terre":   1.8,
    "beton":   2.4,
    "eau":     1.0,
    "gravier": 1.6,
}

# Coûts unitaires réseau (€HT/ml) : [min, max]
_COUTS_RESEAU: dict[str, list[float]] = {
    "eau_potable":    [150, 350],
    "assainissement": [200, 500],
    "pluvial":        [180, 420],
    "telecom":         [80, 180],
}


def calculer_volume(longueur_m: float, largeur_m: float,
                    profondeur_m: float, materiau: str = "terre") -> dict:
    """
    Calcule volume et masse d'un ouvrage rectangulaire.
    Analogie : le géomètre du chantier qui fait son cubature.
    """
    volume_m3 = longueur_m * largeur_m * profondeur_m
    densite = _DENSITES.get(materiau, 1.8)
    masse_t = volume_m3 * densite

    return {
        "volume_m3":  round(volume_m3, 2),
        "masse_t":    round(masse_t, 2),
        "materiau":   materiau,
        "dimensions": f"{longueur_m}m × {largeur_m}m × {profondeur_m}m",
    }


def estimer_cout_reseau(type_reseau: str, longueur_m: float,
                         diametre_mm: float = 200) -> dict:
    """
    Estimation budgétaire d'un réseau TP.
    Analogie : devis rapide de l'entreprise canalisateur.
    """
    fourchette = _COUTS_RESEAU.get(type_reseau, [200, 500])

    # Coefficient diamètre : plus gros = plus cher (loi quadratique simplifiée)
    coeff_diam = math.sqrt(diametre_mm / 200)
    cout_min = round(fourchette[0] * longueur_m * coeff_diam)
    cout_max = round(fourchette[1] * longueur_m * coeff_diam)

    return {
        "type_reseau":  type_reseau,
        "longueur_m":   longueur_m,
        "diametre_mm":  diametre_mm,
        "cout_min_ht":  f"{cout_min:,} €HT".replace(",", " "),
        "cout_max_ht":  f"{cout_max:,} €HT".replace(",", " "),
        "note":         "Fourniture et pose, hors VRD et déviations",
    }


def memo_chantier(cle: str, valeur: str) -> dict:
    """
    Stocke une information dans le journal de session.
    Analogie : noter dans le carnet de chantier.
    """
    _journal_chantier[cle] = valeur
    logger.info(f"📓 Journal chantier — '{cle}' mémorisé")
    return {
        "status":  "mémorisé",
        "cle":     cle,
        "journal": _journal_chantier,
    }


# Registre des outils : nom → fonction Python
_TOOL_REGISTRY: dict[str, Any] = {
    "calculer_volume":    calculer_volume,
    "estimer_cout_reseau": estimer_cout_reseau,
    "memo_chantier":      memo_chantier,
}


def executer_outil(tool_name: str, tool_input: dict) -> str:
    """
    Dispatch : reçoit l'appel outil du modèle, exécute la bonne fonction.
    Analogie BTP : le dispatcher du chantier qui envoie la bonne équipe.

    Args:
        tool_name:  Nom de l'outil demandé par le modèle
        tool_input: Paramètres fournis par le modèle

    Returns:
        Résultat sérialisé en JSON string (pour renvoi au modèle)
    """
    if tool_name not in _TOOL_REGISTRY:
        return json.dumps({"erreur": f"Outil inconnu : {tool_name}"})

    try:
        fn = _TOOL_REGISTRY[tool_name]
        resultat = fn(**tool_input)
        logger.info(f"🔧 Outil '{tool_name}' exécuté → {resultat}")
        return json.dumps(resultat, ensure_ascii=False)
    except Exception as e:
        erreur = {"erreur": str(e), "outil": tool_name, "input": tool_input}
        logger.error(f"❌ Erreur outil '{tool_name}' : {e}")
        return json.dumps(erreur)


# ═══════════════════════════════════════════════════════════════
# BOUCLE AGENTIQUE PRINCIPALE
# Analogie BTP : la réunion de chantier hebdomadaire en boucle
# jusqu'à ce que tout soit validé.
# ═══════════════════════════════════════════════════════════════

def run_agent(
    task: str,
    model: str = "claude-sonnet-4-6",
    max_iterations: int = 10,
    verbose: bool = True,
) -> str:
    """
    Boucle agentique principale.

    Mécanisme :
        1. Envoie la tâche au modèle avec les outils disponibles
        2. Si le modèle répond avec tool_use → on exécute l'outil
        3. On renvoie le résultat au modèle (tool_result)
        4. On répète jusqu'à stop_reason == 'end_turn' ou max_iterations

    Analogie BTP :
        Réunion de chantier → CdT donne des ordres (tool_use)
        → Sous-traitants exécutent (executer_outil)
        → Comptes-rendus remontés (tool_result)
        → CdT synthétise → livraison finale (end_turn)

    Args:
        task:           La mission à accomplir
        model:          Modèle Anthropic à utiliser
        max_iterations: Nombre max d'itérations pour éviter les boucles infinies
        verbose:        Afficher les détails de la boucle

    Returns:
        Réponse finale de l'agent (texte)
    """
    client = anthropic.Anthropic()  # Lit ANTHROPIC_API_KEY depuis l'env

    # System prompt : identité et instructions de l'agent
    system_prompt = """Tu es un assistant expert en travaux publics et ingénierie TP.
Tu aides à calculer des volumes, estimer des coûts de réseaux et synthétiser des analyses chantier.
Utilise les outils disponibles pour répondre avec précision.
Mémorise les résultats importants dans le journal de chantier.
Réponds en français, de manière professionnelle et structurée.
Termine toujours par un récapitulatif clair des résultats."""

    # Historique de la conversation (accumule les tours)
    messages: list[dict] = [
        {"role": "user", "content": task}
    ]

    logger.info(f"🚀 Agent démarré — Modèle : {model}")
    logger.info(f"📋 Mission : {task[:80]}...")

    iteration = 0
    reponse_finale = ""

    # ── BOUCLE AGENTIQUE ───────────────────────────────────────
    while iteration < max_iterations:
        iteration += 1
        if verbose:
            print(f"\n{'─'*50}")
            print(f"  🔄 ITÉRATION {iteration}/{max_iterations}")
            print(f"{'─'*50}")

        # Appel API — on envoie l'historique complet à chaque tour
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        if verbose:
            logger.info(f"📡 Réponse — stop_reason: {response.stop_reason}")

        # ── CAS 1 : Le modèle a terminé (end_turn) ──────────────
        if response.stop_reason == "end_turn":
            # Extraire le texte final
            for block in response.content:
                if hasattr(block, "text"):
                    reponse_finale = block.text
                    break

            print(f"\n{'═'*50}")
            print("  ✅ LIVRAISON FINALE DE L'AGENT")
            print(f"{'═'*50}")
            print(reponse_finale)

            if _journal_chantier:
                print(f"\n📓 Journal de chantier :")
                for k, v in _journal_chantier.items():
                    print(f"   • {k}: {v}")
            break

        # ── CAS 2 : Le modèle veut utiliser des outils (tool_use) ─
        elif response.stop_reason == "tool_use":
            # Ajouter la réponse du modèle à l'historique
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Collecter tous les tool_results de cette itération
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    if verbose:
                        print(f"\n  🔧 Outil demandé : {block.name}")
                        print(f"     Paramètres   : {json.dumps(block.input, ensure_ascii=False)}")

                    # Exécuter l'outil
                    result_str = executer_outil(block.name, block.input)

                    if verbose:
                        print(f"     Résultat     : {result_str}")

                    # Construire le tool_result pour ce tool_use
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result_str,
                    })

            # Renvoyer tous les résultats d'outils au modèle
            messages.append({
                "role": "user",
                "content": tool_results
            })

        # ── CAS 3 : Stop inattendu ───────────────────────────────
        else:
            logger.warning(f"⚠️  Stop inattendu : {response.stop_reason}")
            break

    # Sécurité : si on a dépassé max_iterations
    if iteration >= max_iterations and not reponse_finale:
        logger.warning("⚠️  Max itérations atteint — arrêt forcé")
        reponse_finale = "Agent arrêté : limite d'itérations atteinte."

    return reponse_finale


# ═══════════════════════════════════════════════════════════════
# CLI — Interface ligne de commande
# ═══════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    """Parse les arguments CLI."""
    parser = argparse.ArgumentParser(
        description="Agent TP agentique — Démonstrateur SDK Anthropic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python agent_travaux_src.py
  python agent_travaux_src.py --task "Calcule le volume d'un bassin 50x20x3m en béton"
  python agent_travaux_src.py --model claude-haiku-4-5-20251001 --max-iterations 5
        """,
    )
    parser.add_argument(
        "--task",
        type=str,
        default=(
            "J'ai un chantier avec : un bassin de rétention de 60m×25m×2.5m en béton, "
            "et 350ml de réseau d'assainissement DN300. "
            "Calcule le volume du bassin, estime le coût du réseau, "
            "et mémorise les deux résultats dans le journal de chantier. "
            "Donne-moi ensuite une synthèse chiffrée."
        ),
        help="Mission à donner à l'agent",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-6",
        help="Modèle Anthropic (défaut: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Nombre max d'itérations de la boucle agentique (défaut: 10)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Mode silencieux — affiche uniquement la réponse finale",
    )
    return parser.parse_args()


def main() -> int:
    """Point d'entrée principal."""
    args = parse_args()

    # Vérification clé API
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("❌ ANTHROPIC_API_KEY non trouvée. Créez un .env avec cette variable.")
        print("\n💡 Créez un fichier .env :")
        print('   echo "ANTHROPIC_API_KEY=sk-ant-..." > .env')
        return 1

    print(f"\n{'═'*60}")
    print("  🏗️  AGENT TRAVAUX PUBLICS — SDK ANTHROPIC")
    print(f"  Modèle : {args.model}")
    print(f"  Date   : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═'*60}")

    try:
        run_agent(
            task=args.task,
            model=args.model,
            max_iterations=args.max_iterations,
            verbose=not args.quiet,
        )
        return 0

    except anthropic.AuthenticationError:
        logger.error("❌ Clé API invalide. Vérifiez ANTHROPIC_API_KEY dans .env")
        return 1
    except anthropic.RateLimitError:
        logger.error("❌ Rate limit atteint. Attendez quelques secondes.")
        return 1
    except Exception as e:
        logger.error(f"❌ Erreur inattendue : {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
