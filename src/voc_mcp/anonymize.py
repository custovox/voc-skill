"""Rule-based pseudonymisation of customer feedback (GDPR-minded).

Personal data is replaced by typed placeholders such as ``[EMAIL]`` or
``[NAME]`` so that the analysis keeps its meaning while the person can no
longer be identified directly.

Design choices
--------------
* Standard library only (``re``): no model download, works offline.
* Patterns cover French and English formats (phones, addresses, IBAN...).
* Order matters: the most specific patterns (e-mail, IBAN, card) run first so
  that a broader pattern (long digit run) does not swallow them.
* This is *best-effort* masking, not a legal guarantee. Free-text names are the
  hardest part; we rely on civility titles, self-introductions and a list of
  common first names. A human or the agent should still review the output.
"""

from __future__ import annotations

import re
from collections import Counter

# --------------------------------------------------------------------------
# Building blocks
# --------------------------------------------------------------------------
UPPER = "A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸÆŒ"
# A capitalised word, e.g. "Dupont", "Le-Goff", "O'Neil", "DUPONT"
CAP_WORD = rf"[{UPPER}][^\W\d_]*(?:['’-][^\W\d_]+)*"

# Common first names (French + English). Ambiguous words that are also common
# nouns or adjectives (Rose, Grace, Max, May, Will...) are deliberately left out
# to limit false positives.
FIRST_NAMES = {
    # French
    "Adam", "Adèle", "Agnès", "Alain", "Alexandre", "Alexis", "Alice", "Aline",
    "Amandine", "Amélie", "André", "Anne", "Annie", "Antoine", "Arnaud", "Arthur",
    "Audrey", "Aurélie", "Baptiste", "Benjamin", "Benoît", "Bernard", "Brigitte",
    "Bruno", "Camille", "Caroline", "Catherine", "Cécile", "Céline", "Chantal",
    "Charles", "Charlotte", "Chloé", "Christian", "Christine", "Christophe",
    "Claire", "Claude", "Clément", "Colette", "Corinne", "Cyril", "Damien",
    "Daniel", "David", "Delphine", "Denis", "Didier", "Dominique", "Dylan",
    "Éléonore", "Élise", "Élodie", "Émilie", "Emma", "Emmanuel", "Enzo", "Éric",
    "Estelle", "Étienne", "Fabien", "Fabrice", "Fanny", "Florence", "Florian",
    "Francis", "Franck", "François", "Françoise", "Frédéric", "Gabriel",
    "Gaëlle", "Geneviève", "Georges", "Gérard", "Gilles", "Guillaume", "Hélène",
    "Henri", "Hugo", "Inès", "Isabelle", "Jacqueline", "Jacques", "Jean",
    "Jeanne", "Jérémy", "Jérôme", "Joël", "Jonathan", "Josiane", "Julie",
    "Julien", "Juliette", "Justine", "Karine", "Kevin", "Laetitia", "Laure",
    "Laurence", "Laurent", "Léa", "Léo", "Léon", "Lina", "Louis", "Louise",
    "Luc", "Lucas", "Lucie", "Ludovic", "Manon", "Marc", "Marcel", "Margaux",
    "Marie", "Marine", "Martine", "Mathieu", "Mathilde", "Matthieu", "Maxime",
    "Mélanie", "Michel", "Michèle", "Monique", "Nadia", "Nathalie", "Nicolas",
    "Nicole", "Noémie", "Océane", "Olivier", "Pascal", "Pascale", "Patrice",
    "Patricia", "Patrick", "Paul", "Pauline", "Philippe", "Pierre", "Quentin",
    "Raphaël", "Rémi", "Renée", "Richard", "Robert", "Romain", "Sabrina",
    "Samuel", "Sandrine", "Sarah", "Sébastien", "Serge", "Simon", "Sophie",
    "Stéphane", "Stéphanie", "Suzanne", "Sylvie", "Théo", "Thierry", "Thomas",
    "Valérie", "Véronique", "Vincent", "Virginie", "Yann", "Yannick", "Yves",
    "Zoé", "Mohamed", "Karim", "Yasmine", "Fatima", "Sofiane", "Leïla",
    # English
    "Alex", "Amanda", "Amy", "Andrew", "Anna", "Ashley", "Barbara", "Brian",
    "Chris", "Christopher", "Daniel", "Elizabeth", "Emily", "Emma", "Eric",
    "George", "Hannah", "Jack", "James", "Jason", "Jennifer", "Jessica",
    "John", "Jonathan", "Joseph", "Joshua", "Karen", "Kate", "Kevin", "Laura",
    "Linda", "Lisa", "Mary", "Matthew", "Megan", "Melissa", "Michael", "Nancy",
    "Olivia", "Oliver", "Patricia", "Rachel", "Rebecca", "Robert", "Ryan",
    "Samantha", "Sarah", "Sophia", "Stephanie", "Steven", "Susan", "Thomas",
    "William", "David", "Peter", "Paul", "Helen", "Jane", "Lucy",
}
_FIRST_NAMES_RE = "|".join(sorted((re.escape(n) for n in FIRST_NAMES), key=len, reverse=True))

# --------------------------------------------------------------------------
# Patterns, applied in this order. Each entry: (placeholder, compiled regex).
# --------------------------------------------------------------------------
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    # IBAN: 2 letters, 2 digits, then 11-30 alphanumerics possibly grouped by 4
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){2,7}(?:[ ]?[A-Z0-9]{1,4})?\b")),
    # Payment card: 13-19 digits, optionally separated by spaces or dashes
    ("CARD", re.compile(r"\b(?:\d[ -]?){12,18}\d\b")),
    # Phones: French national/international, then generic international, then US
    ("PHONE", re.compile(
        r"(?:(?:\+|00)33[\s.-]?|\b0)[1-9](?:[\s.-]?\d{2}){4}\b"
        r"|\+\d{1,3}[\s.-]?\(?\d{1,4}\)?(?:[\s.-]?\d{2,4}){2,4}\b"
        r"|\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b"
    )),
    # Street addresses (FR: "12 bis rue de la Paix", EN: "221 Baker Street")
    ("ADDRESS", re.compile(
        r"\b\d{1,4}(?:\s?(?:bis|ter))?,?\s+"
        r"(?:rue|avenue|av\.|boulevard|bd|chemin|allée|allee|impasse|place|route|quai|cours|square|résidence|lotissement)"
        rf"(?:\s+(?:(?:de|du|des|la|le|les|d['’]|l['’])\s*)*{CAP_WORD})+",
        re.IGNORECASE,
    )),
    ("ADDRESS", re.compile(
        rf"\b\d{{1,5}}\s+(?:{CAP_WORD}\s+){{1,3}}"
        r"(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Boulevard|Blvd|Court|Ct|Way)\b"
    )),
    # French postcode + city ("75011 Paris", "69003 Lyon-Part-Dieu")
    ("ADDRESS", re.compile(rf"\b\d{{5}}\s+{CAP_WORD}(?:[\s-]{CAP_WORD})*")),
    # Order / contract / customer references: letters + digits ("CMD-2025-58321")
    ("ID", re.compile(r"\b(?=[A-Z0-9-]*\d)[A-Z]{1,6}[-_]?\d[A-Z0-9-]{3,}\b")),
    # Long digit runs that survived the patterns above (references, accounts)
    ("ID", re.compile(r"\b\d{6,}\b")),
    # Names after a civility title ("Mme Dupont", "M. Jean Martin", "Mr Smith")
    ("NAME", re.compile(
        r"\b(?:M\.|Mme\.?|Mlle\.?|Monsieur|Madame|Mademoiselle|Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Docteur)"
        rf"\s+{CAP_WORD}(?:\s+{CAP_WORD})?"
    )),
    # Self-introductions ("je m'appelle Julie", "my name is John")
    ("NAME", re.compile(
        r"(?i:je\s+m['’]appelle|moi\s+c['’]est|my\s+name\s+is|this\s+is)"
        rf"\s+{CAP_WORD}(?:\s+{CAP_WORD})?"
    )),
    # Known first name, optionally followed by a capitalised surname
    ("NAME", re.compile(rf"\b(?:{_FIRST_NAMES_RE})\b(?:\s+[{UPPER}]{{2,}}\b|\s+{CAP_WORD})?")),
]

# Words that keep their place in the sentence when they introduce a name.
_KEEP_PREFIX = re.compile(
    r"^(?i:(je\s+m['’]appelle|moi\s+c['’]est|my\s+name\s+is|this\s+is|"
    r"M\.|Mme\.?|Mlle\.?|Monsieur|Madame|Mademoiselle|Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Docteur))\s+"
)

# Words that must never be masked as surnames when they follow a first name.
_NOT_SURNAMES = {
    "Bonjour", "Merci", "Je", "Nous", "Vous", "Le", "La", "Les", "Un", "Une",
    "Hello", "Thanks", "The", "I", "We", "You", "Et", "And", "Client", "Agent",
}


def _replace(placeholder: str, match: re.Match[str]) -> str:
    """Build the replacement, keeping civility titles and intro phrases."""
    text = match.group(0)
    if placeholder != "NAME":
        return f"[{placeholder}]"
    prefix = _KEEP_PREFIX.match(text)
    keep = prefix.group(0) if prefix else ""
    # "Julie Bonjour" -> only "Julie" is a name
    tail_words = text[len(keep):].split()
    suffix = ""
    if len(tail_words) == 2 and tail_words[1] in _NOT_SURNAMES:
        suffix = " " + tail_words[1]
    return f"{keep}[NAME]{suffix}"


def anonymize_text(text: str) -> tuple[str, Counter]:
    """Mask personal data in ``text``.

    Returns the masked text and a Counter of replacements per type,
    e.g. ``Counter({'EMAIL': 1, 'PHONE': 2})``.
    """
    counts: Counter = Counter()
    if not text:
        return text, counts
    for placeholder, pattern in PATTERNS:
        def repl(m: re.Match[str], ph: str = placeholder) -> str:
            # Never re-mask an existing placeholder such as "[EMAIL]"
            if m.group(0).startswith("[") and m.group(0).endswith("]"):
                return m.group(0)
            counts[ph] += 1
            return _replace(ph, m)

        text = pattern.sub(repl, text)
    # "[ADDRESS] [ADDRESS]" (street + postcode/city) reads better as one placeholder
    text = re.sub(r"\[ADDRESS\](?:[ ,]+\[ADDRESS\])+", "[ADDRESS]", text)
    return text, counts
