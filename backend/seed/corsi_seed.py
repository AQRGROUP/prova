"""Tabella di partenza corsi e regole mansione -> corsi.

PLACEHOLDER DA VALIDARE COL CLIENTE. Basata sullo schema generale del Nuovo
Accordo Stato-Regioni (formazione lavoratori/dirigenti/preposti, RSPP, addetti
antincendio e primo soccorso) più il modulo HACCP per alimentaristi. I
`codice_sku` sono vuoti: vanno completati con gli SKU reali della piattaforma
prima di generare export utilizzabili.

Ogni corso ha una `chiave` interna stabile (usata dalle regole sotto) che non
dipende dallo SKU, così le regole restano valide anche prima di conoscere gli
SKU reali.
"""

CORSI = [
    {"chiave": "gen_lav", "nome": "Formazione Generale Lavoratori", "categoria": "generale", "ore": 4, "validita_mesi": None},
    {"chiave": "spec_basso", "nome": "Formazione Specifica Lavoratori - Rischio Basso", "categoria": "specifica", "ore": 4, "validita_mesi": 60},
    {"chiave": "spec_medio", "nome": "Formazione Specifica Lavoratori - Rischio Medio", "categoria": "specifica", "ore": 8, "validita_mesi": 60},
    {"chiave": "spec_alto", "nome": "Formazione Specifica Lavoratori - Rischio Alto", "categoria": "specifica", "ore": 12, "validita_mesi": 60},
    {"chiave": "aggiorn_spec", "nome": "Aggiornamento Formazione Specifica", "categoria": "aggiornamento", "ore": 6, "validita_mesi": 60},
    {"chiave": "preposti", "nome": "Formazione Preposti", "categoria": "preposti", "ore": 8, "validita_mesi": 24},
    {"chiave": "dirigenti", "nome": "Formazione Dirigenti", "categoria": "dirigenti", "ore": 16, "validita_mesi": 60},
    {"chiave": "rspp_dl_basso", "nome": "RSPP Datore di Lavoro - Rischio Basso", "categoria": "rspp_dl", "ore": 16, "validita_mesi": 60},
    {"chiave": "rspp_dl_medio", "nome": "RSPP Datore di Lavoro - Rischio Medio", "categoria": "rspp_dl", "ore": 32, "validita_mesi": 60},
    {"chiave": "rspp_dl_alto", "nome": "RSPP Datore di Lavoro - Rischio Alto", "categoria": "rspp_dl", "ore": 48, "validita_mesi": 60},
    {"chiave": "rspp_aspp_modulo_a", "nome": "RSPP/ASPP Modulo A", "categoria": "rspp_aspp", "ore": 28, "validita_mesi": 60},
    {"chiave": "antincendio_basso", "nome": "Addetto Antincendio - Rischio Basso", "categoria": "antincendio", "ore": 4, "validita_mesi": 60},
    {"chiave": "antincendio_medio", "nome": "Addetto Antincendio - Rischio Medio", "categoria": "antincendio", "ore": 8, "validita_mesi": 60},
    {"chiave": "antincendio_alto", "nome": "Addetto Antincendio - Rischio Alto", "categoria": "antincendio", "ore": 16, "validita_mesi": 60},
    {"chiave": "primo_soccorso_bc", "nome": "Addetto Primo Soccorso - Gruppo B/C", "categoria": "primo_soccorso", "ore": 12, "validita_mesi": 36},
    {"chiave": "primo_soccorso_a", "nome": "Addetto Primo Soccorso - Gruppo A", "categoria": "primo_soccorso", "ore": 16, "validita_mesi": 36},
    {"chiave": "haccp", "nome": "HACCP - Alimentaristi/Manipolazione Alimenti", "categoria": "haccp", "ore": 4, "validita_mesi": 36},
]

# Ogni regola: se la mansione contiene una delle parole chiave (case-insensitive),
# si applicano i corsi elencati. Le regole sono valutate in ordine e sono
# cumulative: una mansione può far scattare più regole (es. "capo cuoco" ->
# rischio medio + preposti + haccp).
MANSIONE_RULES = [
    {
        "parole_chiave": ["operaio", "manovale", "muratore", "carpentiere", "magazziniere", "edile", "cantiere"],
        "rischio": "alto",
        "corsi": ["gen_lav", "spec_alto"],
    },
    {
        "parole_chiave": ["impiegato", "amministrativ", "segretari", "ufficio", "contabil"],
        "rischio": "basso",
        "corsi": ["gen_lav", "spec_basso"],
    },
    {
        "parole_chiave": ["commesso", "cassiere", "banconista", "addetto vendita"],
        "rischio": "basso",
        "corsi": ["gen_lav", "spec_basso"],
    },
    {
        "parole_chiave": ["cameriere", "barista", "sala", "bar"],
        "rischio": "medio",
        "corsi": ["gen_lav", "spec_medio", "haccp"],
    },
    {
        "parole_chiave": ["cuoco", "pizzaiolo", "gelataio", "panettiere", "pasticcere", "manipolatore aliment", "cucina"],
        "rischio": "medio",
        "corsi": ["gen_lav", "spec_medio", "haccp"],
    },
    {
        # Lavorazione/confezionamento alimentare (es. industria carni, ATECO 10.x):
        # rischio alto per macchinari di sezionamento, più HACCP obbligatorio.
        "parole_chiave": ["disossatore", "macellaio", "macellazione", "sezionatore", "impacchettamento", "confezionamento aliment"],
        "rischio": "alto",
        "corsi": ["gen_lav", "spec_alto", "haccp"],
    },
    {
        "parole_chiave": ["pulizie", "addetto alle pulizie", "addetta alle pulizie"],
        "rischio": "basso",
        "corsi": ["gen_lav", "spec_basso"],
    },
    {
        "parole_chiave": ["preposto", "capo reparto", "caposquadra", "responsabile di cantiere"],
        "rischio": None,
        "corsi": ["preposti"],
    },
    {
        "parole_chiave": ["dirigente", "direttore"],
        "rischio": None,
        "corsi": ["dirigenti"],
    },
    {
        "parole_chiave": ["rspp", "responsabile servizio prevenzione"],
        "rischio": None,
        "corsi": ["rspp_aspp_modulo_a"],
    },
]
