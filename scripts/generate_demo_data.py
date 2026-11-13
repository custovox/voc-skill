"""Generate the fictional demo dataset for "Maison Verveine", an imaginary French
direct-to-consumer brand of natural cosmetics.

Everything here is invented: brand, products, customers, names, e-mails, phone
numbers, addresses and order numbers. Personal data is planted on purpose in some
reviews to demonstrate the anonymisation step.

The dataset has a known "ground truth" (see GROUND_TRUTH below) so that the
analysis can be checked: a carrier change in July 2026 creates delivery delays,
glass jars break in transit, a new pump leaks from August, and a weak signal
(skin redness with the reformulated night cream) appears in September only.

Usage:  python scripts/generate_demo_data.py   (writes examples/data/avis_ecommerce.csv)
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 2026
N_REVIEWS = 200
OUT = Path(__file__).resolve().parent.parent / "examples" / "data" / "avis_ecommerce.csv"

PRODUCTS = ["Crème Nuit Réparatrice", "Sérum Éclat Verveine", "Savon Surgras Verveine",
            "Huile Sèche Corps", "Baume Lèvres", "Shampooing Solide", "Coffret Découverte",
            "Crème Mains Verveine"]
CHANNELS = [("site", 0.55), ("application", 0.15), ("enquête e-mail", 0.15),
            ("réseaux sociaux", 0.08), ("marketplace", 0.07)]

GROUND_TRUTH = {
    "retard_livraison": "delivery delays, mostly from July 2026 (carrier change)",
    "colis_abime": "broken glass jars / damaged parcels",
    "service_client_injoignable": "customer service hard to reach",
    "remboursement_lent": "slow refunds",
    "prix_frais_port": "price and shipping fees",
    "code_promo": "promo code not working",
    "pompe_fuit": "new pump leaks, from August 2026",
    "reaction_cutanee": "WEAK SIGNAL - redness with the night cream, September 2026 only",
    "recharges": "WEAK SIGNAL / opportunity - requests for refills",
}

# ---------------------------------------------------------------------------
# Sentence banks. Each pain point: (intensity 1-5, list of sentences).
# ---------------------------------------------------------------------------
PAIN = {
    "retard_livraison": (3, [
        "Livraison annoncée en 48h, reçue au bout de 9 jours.",
        "Le suivi est resté bloqué sur « en cours d'acheminement » pendant une semaine.",
        "Depuis que vous avez changé de transporteur c'est devenu très long.",
        "Colis livré avec 6 jours de retard, j'ai dû racheter en pharmacie entre temps.",
        "Commande passée pour un anniversaire, arrivée après la date. Dommage.",
        "Le transporteur a marqué « destinataire absent » alors que j'étais chez moi.",
        "Toujours pas reçu ma commande au bout de 12 jours, aucune explication.",
        "Délais de livraison beaucoup plus longs qu'avant, c'est dommage.",
        "Point relais changé sans prévenir, j'ai mis une semaine à retrouver mon colis.",
        "Avant je recevais en 2 jours, maintenant c'est plus d'une semaine.",
    ]),
    "colis_abime": (4, [
        "Le pot en verre est arrivé cassé, de la crème partout dans le carton.",
        "Colis écrasé, le flacon d'huile avait fui sur tout le reste.",
        "Deuxième fois que je reçois un pot fêlé. Le calage est insuffisant.",
        "Emballage joli mais pas protecteur : le verre était en miettes.",
        "Pot cassé à la réception, j'ai failli me couper en ouvrant le colis.",
        "Le couvercle était fendu et la crème avait séché.",
    ]),
    "service_client_injoignable": (4, [
        "Impossible de joindre le service client, 40 minutes d'attente au téléphone.",
        "J'ai envoyé trois e-mails, aucune réponse en dix jours.",
        "Le chat ne répond qu'avec des messages automatiques.",
        "On me promet un rappel qui n'arrive jamais.",
        "Service client aux abonnés absents dès qu'il y a un problème.",
        "J'ai dû appeler quatre fois pour expliquer le même problème.",
    ]),
    "remboursement_lent": (4, [
        "Retour accepté il y a trois semaines, toujours pas remboursée.",
        "On me dit que le remboursement est en cours depuis un mois.",
        "Le remboursement a pris plus de 30 jours, c'est inadmissible.",
        "Remboursement partiel sans explication, j'attends toujours le reste.",
    ]),
    "prix_frais_port": (2, [
        "Produits un peu chers pour la quantité.",
        "Les frais de port à 6,90 € piquent un peu.",
        "Le seuil de livraison gratuite est passé à 59 €, c'est trop.",
        "Bon produit mais le prix a augmenté depuis l'an dernier.",
        "Les formats sont petits pour le prix.",
    ]),
    "code_promo": (2, [
        "Le code promo de la newsletter ne fonctionnait pas.",
        "Code de bienvenue refusé au paiement, j'ai payé plein tarif.",
        "Impossible d'appliquer le code de parrainage.",
    ]),
    "pompe_fuit": (3, [
        "La nouvelle pompe fuit, le produit coule dans la trousse.",
        "Le flacon pompe est arrivé à moitié vide, il fuyait.",
        "Depuis le nouveau flacon la pompe se bloque puis fuit.",
        "Pompe défectueuse, impossible de doser, ça coule de partout.",
    ]),
    "reaction_cutanee": (5, [
        "Depuis la nouvelle formule de la crème de nuit, j'ai des rougeurs sur les joues.",
        "Ma peau a réagi à la Crème Nuit (rougeurs, picotements), ce n'était pas le cas avant.",
        "Picotements et plaques rouges après deux applications de la crème de nuit, j'ai arrêté.",
    ]),
    "recharges": (1, [
        "Ce serait bien de proposer des recharges pour éviter de racheter des pots.",
        "Vous pourriez faire des écorecharges ? Pour une marque naturelle ce serait logique.",
        "J'aimerais pouvoir renvoyer les pots vides ou acheter des recharges.",
        "Dommage qu'il n'existe pas de format recharge.",
    ]),
}

DELIGHT = {
    "efficacite": [
        "Ma peau est plus douce dès la première semaine.",
        "Le sérum a vraiment unifié mon teint, je suis bluffée.",
        "Crème très efficace, ma peau ne tiraille plus.",
        "Résultat visible, mes mains ne sont plus sèches.",
        "Le shampooing solide laisse les cheveux légers et brillants.",
        "Le baume lèvres tient toute la journée.",
        "Peau apaisée et hydratée, exactement ce que je cherchais.",
    ],
    "texture_parfum": [
        "La texture est fondante et pénètre vite.",
        "L'odeur de verveine est fraîche et naturelle, pas écœurante.",
        "Texture légère, non grasse, parfaite sous le maquillage.",
        "Le parfum est discret et agréable.",
        "J'adore le parfum, toute la salle de bain sent bon.",
    ],
    "naturel_valeurs": [
        "Composition courte et naturelle, ça me rassure.",
        "Fabriqué en France avec des ingrédients bio, c'est important pour moi.",
        "J'apprécie l'engagement de la marque sur les emballages.",
        "Enfin une marque transparente sur ses ingrédients.",
    ],
    "livraison_rapide": [
        "Livraison rapide, reçu en 48h.",
        "Colis bien emballé et arrivé très vite.",
        "Commande reçue en deux jours, parfait.",
    ],
    "service_aimable": [
        "Conseillère au téléphone très aimable, problème réglé en 5 minutes.",
        "Le service client m'a renvoyé un produit sans discuter, merci.",
        "Réponse rapide et bienveillante du service client.",
    ],
    "echantillons": [
        "Merci pour les échantillons glissés dans le colis !",
        "Petit mot manuscrit et échantillons offerts, j'ai été touchée.",
    ],
}

OPENINGS_POS = ["", "Très satisfaite !", "Super produit.", "Je recommande.", "Fidèle depuis 2 ans.",
                "Première commande et conquise.", "Rien à redire sur le produit."]
OPENINGS_NEG = ["", "Déçue.", "Franchement pas content.", "Grosse déception.", "Bof.",
                "Je ne recommanderai plus.", "Expérience décevante."]
CLOSINGS_POS = ["", "Je recommanderai.", "Je recommande les yeux fermés.", "Merci Maison Verveine !", ""]
CLOSINGS_NEG = ["", "Dommage car les produits sont bons.", "Je vais aller voir ailleurs.",
                "Je ne sais pas si je recommanderai.", "Il faut vraiment améliorer ça.", ""]
MIXED_LINK = ["Par contre", "En revanche", "Seul bémol :", "Mais"]

# Planted personal data (all invented) to demonstrate anonymisation.
PII_SNIPPETS = [
    "Je suis Mme Lefèvre, commande CMD-2026-48211, merci de me rappeler au 06 47 12 88 30.",
    "Vous pouvez me répondre à sophie.marchal@exemple.fr, commande n° 584213.",
    "Livraison prévue au 14 rue des Tilleuls 69003 Lyon, jamais arrivée.",
    "Claire au service client a été adorable.",
    "Mon numéro client est VRV-778412, je n'ai aucune réponse.",
    "Appelez-moi au +33 7 81 22 45 10, je m'appelle Karim Benali.",
    "M. Durand du SAV m'a promis un rappel.",
    "Remboursement attendu sur mon compte FR76 1027 8060 1100 0204 5670 128.",
    "Adresse : 8 bis avenue Jean Jaurès 31000 Toulouse.",
    "Julien du chat m'a très bien conseillé.",
]


def pick_channel(rng: random.Random) -> str:
    x, acc = rng.random(), 0.0
    for name, p in CHANNELS:
        acc += p
        if x <= acc:
            return name
    return CHANNELS[-1][0]


def pick_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randrange((end - start).days + 1))


def main() -> None:
    rng = random.Random(SEED)
    period_start, period_end = date(2026, 4, 1), date(2026, 9, 30)
    rows = []
    # Planned pain-point counts (the rest are positive or mixed reviews).
    plan = (["retard_livraison"] * 30 + ["colis_abime"] * 20 + ["service_client_injoignable"] * 18
            + ["remboursement_lent"] * 11 + ["prix_frais_port"] * 15 + ["code_promo"] * 7
            + ["pompe_fuit"] * 8 + ["reaction_cutanee"] * 3 + ["recharges"] * 5)
    plan += [None] * (N_REVIEWS - len(plan))
    rng.shuffle(plan)

    pii_slots = set(rng.sample(range(N_REVIEWS), len(PII_SNIPPETS)))
    pii_iter = iter(PII_SNIPPETS)

    for i, pain in enumerate(plan, start=1):
        # Dates follow the scenario of each pain point
        if pain == "retard_livraison":
            d = pick_date(rng, date(2026, 7, 1), period_end) if rng.random() < 0.85 else pick_date(rng, period_start, period_end)
        elif pain == "pompe_fuit":
            d = pick_date(rng, date(2026, 8, 5), period_end)
        elif pain == "reaction_cutanee":
            d = pick_date(rng, date(2026, 9, 8), period_end)
        else:
            d = pick_date(rng, period_start, period_end)

        product = rng.choice(PRODUCTS)
        if pain == "reaction_cutanee":
            product = "Crème Nuit Réparatrice"
        if pain == "pompe_fuit":
            product = rng.choice(["Sérum Éclat Verveine", "Huile Sèche Corps"])

        parts: list[str] = []
        if pain is None:
            # Positive review: 1-2 delight themes
            keys = rng.sample(list(DELIGHT), rng.choice([1, 2]))
            if d >= date(2026, 7, 1) and "livraison_rapide" in keys:
                keys.remove("livraison_rapide")  # fast delivery is rare after the carrier change
                keys = keys or ["efficacite"]
            parts = [rng.choice(OPENINGS_POS)] + [rng.choice(DELIGHT[k]) for k in keys] + [rng.choice(CLOSINGS_POS)]
            rating = rng.choice([5, 5, 5, 4, 4])
        else:
            intensity, bank = PAIN[pain]
            sentence = rng.choice(bank)
            mixed = intensity <= 3 and rng.random() < 0.5 or pain == "recharges"
            if mixed:
                parts = [rng.choice(DELIGHT[rng.choice(["efficacite", "texture_parfum", "naturel_valeurs"])]),
                         rng.choice(MIXED_LINK) + " " + sentence[0].lower() + sentence[1:]]
                rating = 4 if intensity <= 2 else 3
            else:
                parts = [rng.choice(OPENINGS_NEG), sentence, rng.choice(CLOSINGS_NEG)]
                rating = {1: 4, 2: 3, 3: rng.choice([2, 3]), 4: rng.choice([1, 2]), 5: 1}[intensity]
            # Some customers combine two problems (e.g. late parcel + unreachable service)
            if pain in ("retard_livraison", "colis_abime", "remboursement_lent") and rng.random() < 0.25:
                parts.insert(-1, rng.choice(PAIN["service_client_injoignable"][1]))
            # Avoid contradictory or repetitive endings ("Je ne recommanderai plus ... Je recommanderai")
            if len(parts) >= 2 and "recommand" in parts[-1] and any("recommand" in p for p in parts[:-1]):
                parts[-1] = ""
            if len(parts) >= 2 and parts[-1].startswith("Dommage") and "Dommage" in " ".join(parts[:-1]):
                parts[-1] = ""
        if i - 1 in pii_slots:
            parts.insert(-1, next(pii_iter))
        text = " ".join(p for p in parts if p).replace(" :  ", " : ")
        rows.append({"id": f"AV-{i:04d}", "date": d.strftime("%d/%m/%Y"), "note": rating,
                     "canal": pick_channel(rng), "produit": product, "avis": text})

    rows.sort(key=lambda r: (r["date"][6:], r["date"][3:5], r["date"][:2]))
    for i, r in enumerate(rows, start=1):  # ids follow chronological order
        r["id"] = f"AV-{i:04d}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "date", "note", "canal", "produit", "avis"], delimiter=";")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} reviews to {OUT}")


if __name__ == "__main__":
    main()
