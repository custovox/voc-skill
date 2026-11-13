from voc_mcp.anonymize import anonymize_text


def test_email_phone_and_civility_name():
    text, counts = anonymize_text(
        "Je suis Mme Dupont, écrivez à claire.d@exemple.fr ou appelez le 06 12 34 56 78."
    )
    assert text == "Je suis Mme [NAME], écrivez à [EMAIL] ou appelez le [PHONE]."
    assert counts == {"NAME": 1, "EMAIL": 1, "PHONE": 1}


def test_international_and_us_phones():
    text, _ = anonymize_text("Call +44 20 7946 0958 or (555) 123-4567, or +33 7 81 22 45 10.")
    assert "[PHONE]" in text and "7946" not in text and "555" not in text and "81 22" not in text


def test_address_and_order_numbers():
    text, counts = anonymize_text("Livré au 12 bis rue de la Paix 75002 Paris, commande CMD-2026-58321, contrat 88451234.")
    assert "Paix" not in text and "Paris" not in text
    assert "58321" not in text and "88451234" not in text
    assert counts["ADDRESS"] == 2 and counts["ID"] == 2


def test_iban_and_card():
    text, counts = anonymize_text("IBAN FR76 3000 6000 0112 3456 7890 189, carte 4970 1012 3456 7890")
    assert text == "IBAN [IBAN], carte [CARD]"
    assert counts == {"IBAN": 1, "CARD": 1}


def test_first_names_and_self_introduction():
    text, _ = anonymize_text("Je m'appelle Karim Benali. Merci à Julie Bonjour du SAV ! My name is John Smith.")
    assert text == "Je m'appelle [NAME]. Merci à [NAME] Bonjour du SAV ! My name is [NAME]."


def test_business_words_are_kept():
    original = "La crème SPF50 est livrée en 48h, note 4/5, le 12/03/2026, prix 29,90 €."
    text, counts = anonymize_text(original)
    assert text == original
    assert not counts


def test_placeholders_are_stable():
    once, _ = anonymize_text("Mail : a.b@exemple.fr, Mme Martin")
    twice, counts = anonymize_text(once)
    assert once == twice
    assert not counts
