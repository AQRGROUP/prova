from app.services.corsi_matcher import corsi_per_mansione


def test_operaio_rischio_alto():
    corsi = corsi_per_mansione("Operaio edile")
    chiavi = [c.chiave for c in corsi]
    assert chiavi == ["gen_lav", "spec_alto"]


def test_cuoco_include_haccp():
    corsi = corsi_per_mansione("Cuoco")
    chiavi = {c.chiave for c in corsi}
    assert chiavi == {"gen_lav", "spec_medio", "haccp"}


def test_disossatore_lavorazione_carne():
    corsi = corsi_per_mansione("Disossatore")
    chiavi = {c.chiave for c in corsi}
    assert chiavi == {"gen_lav", "spec_alto", "haccp"}


def test_mansione_sconosciuta_nessun_corso():
    assert corsi_per_mansione("Astronauta") == []


def test_match_case_insensitive():
    corsi_maiuscolo = corsi_per_mansione("CUOCO")
    corsi_minuscolo = corsi_per_mansione("cuoco")
    assert {c.chiave for c in corsi_maiuscolo} == {c.chiave for c in corsi_minuscolo}


def test_preposto_e_cumulativo_con_mansione_operativa():
    # una mansione può far scattare più regole contemporaneamente
    corsi = corsi_per_mansione("Capo reparto operaio")
    chiavi = {c.chiave for c in corsi}
    assert "preposti" in chiavi
    assert "gen_lav" in chiavi
