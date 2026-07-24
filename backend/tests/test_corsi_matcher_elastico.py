from app.services.corsi_matcher import corsi_per_mansione_elastico


def test_mansione_nota_non_richiede_verifica():
    corsi, da_verificare = corsi_per_mansione_elastico("Operaio edile")
    assert da_verificare is False
    assert len(corsi) == 2


def test_mansione_sconosciuta_senza_ai_disponibile_richiede_verifica(monkeypatch):
    monkeypatch.setattr("app.services.corsi_matcher.classifica_mansione_ai", lambda mansione: None)

    corsi, da_verificare = corsi_per_mansione_elastico("Saldatore su banco prova")

    assert da_verificare is True
    assert corsi == []


def test_mansione_sconosciuta_con_suggerimento_ai_e_comunque_da_verificare(monkeypatch):
    monkeypatch.setattr(
        "app.services.corsi_matcher.classifica_mansione_ai",
        lambda mansione: {"rischio": "alto", "richiede_haccp": False},
    )

    corsi, da_verificare = corsi_per_mansione_elastico("Saldatore su banco prova")

    assert da_verificare is True
    chiavi = {c.chiave for c in corsi}
    assert chiavi == {"gen_lav", "spec_alto"}


def test_mansione_sconosciuta_con_suggerimento_haccp(monkeypatch):
    monkeypatch.setattr(
        "app.services.corsi_matcher.classifica_mansione_ai",
        lambda mansione: {"rischio": "medio", "richiede_haccp": True},
    )

    corsi, da_verificare = corsi_per_mansione_elastico("Addetto alla mensa scolastica")

    assert da_verificare is True
    chiavi = {c.chiave for c in corsi}
    assert chiavi == {"gen_lav", "spec_medio", "haccp"}
