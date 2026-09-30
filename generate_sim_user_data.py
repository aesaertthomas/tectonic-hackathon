"""Generate sim-user-data.json: 24 months of synthetic Belgian banking history.

Deterministic (fixed seed). Run: python3 generate_sim_user_data.py
"""
import calendar
import json
import random
from collections import defaultdict
from pathlib import Path

SEED = 20260930
START = (2024, 10)
N_MONTHS = 24
OUT = Path(__file__).with_name("sim-user-data.json")

# Rough price/wage indexation relative to 2026 levels.
YEAR_FACTOR = {2024: 0.95, 2025: 0.975, 2026: 1.0}

# Holiday/seasonal multipliers reused across profiles.
DECEMBER = {12: 1.35}
SUMMER = {7: 1.6, 8: 1.3}
SALES = {1: 1.4, 7: 1.3}


def months():
    y, m = START
    for _ in range(N_MONTHS):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def ym(y, m):
    return f"{y:04d}-{m:02d}"


def active(item, key, month):
    return (item.get("from", "0000-00") <= key <= item.get("to", "9999-99")
            and ("months" not in item or month in item["months"]))


# ---------------------------------------------------------------------------
# Profiles. Amounts are 2026 levels in EUR; earlier years are scaled down by
# YEAR_FACTOR for items marked indexed and for all variable spending.
# scheduled: fixed-date items (income, bills, transfers between own accounts)
# variable:  categories spread over several transactions with random dates
# ---------------------------------------------------------------------------
PROFILES = [
    {
        "id": "BE001",
        "name": "Jean Lambert",
        "age": 72,
        "profile": "Elderly person / pensioner",
        "household": "1 personne",
        "location": "Namur, Belgique",
        "income_type": "pension",
        "story": "Stable pensioner. His car loan ends in February 2026 and he redirects the freed-up money to savings: "
                 "monthly transfer goes from EUR 200 to 300 (Mar-Apr 2026) and then EUR 450 (from May 2026). "
                 "Demo journey: sustained saving increase -> goal.",
        "accounts": [
            {"id": "BE001-CUR", "type": "current", "name": "Compte à vue", "opening_balance": 4100.00},
            {"id": "BE001-SAV", "type": "savings", "name": "Compte d'épargne", "opening_balance": 18500.00},
        ],
        "scheduled": [
            {"kind": "income", "merchant": "Service fédéral des Pensions", "category": "pension", "amount": 2300, "day": 1, "indexed": True},
            {"kind": "income", "merchant": "Service fédéral des Pensions - pécule de vacances", "category": "holiday_pay", "amount": 980, "day": 20, "months": [5], "indexed": True},
            {"kind": "expense", "merchant": "Loyer - M. Dubois", "category": "housing_energy", "amount": 590, "day": 3},
            {"kind": "expense", "merchant": "Engie Electrabel", "category": "housing_energy", "amount": 118, "day": 12},
            {"kind": "expense", "merchant": "SWDE eau", "category": "housing_energy", "amount": 28, "day": 18},
            {"kind": "expense", "merchant": "Proximus", "category": "communication", "amount": 54.99, "day": 8},
            {"kind": "expense", "merchant": "Ethias assurance habitation", "category": "insurance_financial_services", "amount": 32, "day": 10},
            {"kind": "expense", "merchant": "Ethias assurance auto", "category": "insurance_financial_services", "amount": 68, "day": 10},
            {"kind": "expense", "merchant": "Assurance hospitalisation DKV", "category": "insurance_financial_services", "amount": 44, "day": 15},
            {"kind": "expense", "merchant": "Mutualité chrétienne cotisation", "category": "healthcare", "amount": 12, "day": 5},
            {"kind": "expense", "merchant": "Frais de gestion compte", "category": "insurance_financial_services", "amount": 6, "day": 28},
            {"kind": "expense", "merchant": "Prêt auto - mensualité", "category": "debt_repayment", "amount": 300, "day": 6, "to": "2026-02"},
            {"kind": "transfer", "merchant": "Épargne mensuelle", "category": "transfer_to_savings", "amount": 200, "day": 2, "to_account": "BE001-SAV", "to": "2026-02"},
            {"kind": "transfer", "merchant": "Épargne mensuelle", "category": "transfer_to_savings", "amount": 300, "day": 2, "to_account": "BE001-SAV", "from": "2026-03", "to": "2026-04"},
            {"kind": "transfer", "merchant": "Épargne mensuelle", "category": "transfer_to_savings", "amount": 450, "day": 2, "to_account": "BE001-SAV", "from": "2026-05"},
        ],
        "variable": [
            {"category": "food", "monthly": 340, "count": (8, 11), "merchants": ["Delhaize", "Colruyt", "Carrefour Market", "Boulangerie Léonard", "Marché de Namur"], "season": DECEMBER},
            {"category": "healthcare", "monthly": 115, "count": (2, 4), "merchants": ["Pharmacie du Centre", "Dr. Mathieu (généraliste)", "Kinésithérapie Namur"], "season": {1: 1.2, 2: 1.2}},
            {"category": "transport", "monthly": 105, "count": (3, 5), "merchants": ["TotalEnergies", "Q8", "TEC Namur", "Parking Namur"]},
            {"category": "leisure_culture", "monthly": 110, "count": (2, 5), "merchants": ["Théâtre Royal de Namur", "Librairie Papyrus", "Club de bridge", "Jardinerie Aveve"], "season": {6: 2.5, 12: 1.4}},
            {"category": "restaurants", "monthly": 60, "count": (1, 3), "merchants": ["Brasserie Henri", "Le Temps des Cerises", "Café du Marché"], "season": DECEMBER},
            {"category": "clothing", "monthly": 45, "count": (0, 2), "merchants": ["C&A", "Damart", "Chaussures Brantano"], "season": SALES},
            {"category": "household_maintenance", "monthly": 65, "count": (1, 3), "merchants": ["Brico", "Action", "Hubo"]},
            {"category": "other", "monthly": 50, "count": (1, 3), "merchants": ["Cadeaux petits-enfants", "Coiffeur Sylvie", "La Poste"], "season": {12: 3.0}},
        ],
        "one_offs": [
            {"date": "2025-03-14", "merchant": "Dentiste Dr. Renard", "category": "healthcare", "amount": -640},
            {"date": "2025-03-28", "merchant": "Mutualité chrétienne remboursement", "category": "healthcare", "amount": 212.40, "type": "refund"},
            {"date": "2025-10-09", "merchant": "Garage Namur - entretien", "category": "transport", "amount": -385},
            {"date": "2026-01-22", "merchant": "Audioprothésiste", "category": "healthcare", "amount": -1150},
            {"date": "2026-02-10", "merchant": "Mutualité chrétienne remboursement", "category": "healthcare", "amount": 520.00, "type": "refund"},
            {"date": "2026-06-11", "merchant": "Voyages Pierrot - séjour Côte d'Opale", "category": "leisure_culture", "amount": -890},
        ],
        "overrides": {},
    },
    {
        "id": "BE002",
        "name": "Sophie & Thomas De Smet",
        "age": 43,
        "profile": "Married couple with 3 children",
        "household": "2 adultes + 3 enfants",
        "location": "Mechelen, België",
        "income_type": "household salaries + child benefit",
        "story": "Two incomes, homeowners with a mortgage, uses a credit card repaid in full every month. "
                 "Holiday pay in May and a 13th month in December fund the summer holiday and Christmas. "
                 "In September 2026 grocery spending jumps to ~EUR 1,420 (usual ~EUR 900-1,000) on top of back-to-school costs. "
                 "Demo journey: grocery spike -> cash-flow scenario.",
        "accounts": [
            {"id": "BE002-CUR", "type": "current", "name": "Zichtrekening", "opening_balance": 2600.00},
            {"id": "BE002-SAV", "type": "savings", "name": "Spaarrekening", "opening_balance": 14000.00},
            {"id": "BE002-CC", "type": "credit_card", "name": "Kredietkaart", "opening_balance": -640.00},
        ],
        "scheduled": [
            {"kind": "income", "merchant": "Salaris - Werkgever Thomas", "category": "salary", "amount": 3150, "day": 28, "indexed": True, "sd": 0.01},
            {"kind": "income", "merchant": "Salaris - Werkgever Sophie", "category": "salary", "amount": 2500, "day": 28, "indexed": True, "sd": 0.01},
            {"kind": "income", "merchant": "Groeipakket - kinderbijslag", "category": "child_benefit", "amount": 550, "day": 10, "indexed": True},
            {"kind": "income", "merchant": "Vakantiegeld - Thomas", "category": "holiday_pay", "amount": 2650, "day": 26, "months": [5], "indexed": True},
            {"kind": "income", "merchant": "Vakantiegeld - Sophie", "category": "holiday_pay", "amount": 2080, "day": 26, "months": [5], "indexed": True},
            {"kind": "income", "merchant": "Eindejaarspremie - Thomas", "category": "year_end_bonus", "amount": 2450, "day": 20, "months": [12], "indexed": True},
            {"kind": "income", "merchant": "Eindejaarspremie - Sophie", "category": "year_end_bonus", "amount": 1940, "day": 20, "months": [12], "indexed": True},
            {"kind": "expense", "merchant": "Hypothecaire lening - maandaflossing", "category": "housing_energy", "amount": 1350, "day": 2},
            {"kind": "expense", "merchant": "Luminus energie", "category": "housing_energy", "amount": 265, "day": 14},
            {"kind": "expense", "merchant": "De Watergroep", "category": "housing_energy", "amount": 58, "day": 20},
            {"kind": "expense", "merchant": "Onroerende voorheffing", "category": "housing_energy", "amount": 1180, "day": 16, "months": [8]},
            {"kind": "expense", "merchant": "Telenet (internet, tv, mobiel)", "category": "communication", "amount": 124.50, "day": 7},
            {"kind": "expense", "merchant": "Orange mobiel", "category": "communication", "amount": 25, "day": 9},
            {"kind": "expense", "merchant": "Woningverzekering", "category": "insurance_financial_services", "amount": 56, "day": 11},
            {"kind": "expense", "merchant": "Autoverzekering", "category": "insurance_financial_services", "amount": 96, "day": 11},
            {"kind": "expense", "merchant": "Hospitalisatieverzekering", "category": "insurance_financial_services", "amount": 72, "day": 15},
            {"kind": "expense", "merchant": "Familiale verzekering", "category": "insurance_financial_services", "amount": 12, "day": 15},
            {"kind": "expense", "merchant": "Bankkosten", "category": "insurance_financial_services", "amount": 9, "day": 28},
            {"kind": "expense", "merchant": "Ziekenfonds bijdrage", "category": "healthcare", "amount": 30, "day": 5},
            {"kind": "expense", "merchant": "NMBS treinabonnement", "category": "transport", "amount": 112, "day": 1},
            {"kind": "expense", "merchant": "Naschoolse opvang", "category": "children_education", "amount": 175, "day": 12, "months": [1, 2, 3, 4, 5, 6, 9, 10, 11, 12]},
            {"kind": "expense", "merchant": "Netflix", "category": "leisure_culture", "amount": 13.99, "day": 18},
            {"kind": "expense", "merchant": "Spotify Family", "category": "leisure_culture", "amount": 20.99, "day": 22},
            {"kind": "transfer", "merchant": "Maandelijkse spaaropdracht", "category": "transfer_to_savings", "amount": 300, "day": 29, "to_account": "BE002-SAV"},
            {"kind": "transfer", "merchant": "Vakantiegeld naar spaarrekening", "category": "transfer_to_savings", "amount": 3500, "day": 27, "to_account": "BE002-SAV", "months": [5]},
            {"kind": "transfer", "merchant": "Eindejaarspremie naar spaarrekening", "category": "transfer_to_savings", "amount": 3200, "day": 22, "to_account": "BE002-SAV", "months": [12]},
            {"kind": "transfer", "merchant": "Spaarrekening naar zichtrekening (zomervakantie)", "category": "transfer_from_savings", "amount": 1500, "day": 3, "from_account": "BE002-SAV", "months": [7]},
        ],
        "variable": [
            {"category": "food", "monthly": 950, "count": (12, 16), "merchants": ["Colruyt", "Albert Heijn", "Delhaize", "Aldi", "Bakkerij Vermeulen"], "season": {12: 1.2, 7: 0.85}, "sd": 0.06},
            {"category": "transport", "monthly": 420, "count": (4, 7), "merchants": ["TotalEnergies", "Shell", "Q8", "De Lijn", "Interparking"], "season": {7: 1.5}},
            {"category": "children_education", "monthly": 240, "count": (2, 5), "merchants": ["Schoolfactuur", "Muziekacademie", "Voetbalclub KV Mechelen jeugd", "Standaard Boekhandel"], "season": {9: 2.6, 10: 1.3, 7: 0.3, 8: 0.6}},
            {"category": "healthcare", "monthly": 230, "count": (2, 5), "merchants": ["Apotheek De Linde", "Huisartsenpraktijk Mechelen", "Tandarts Peeters", "Kinesist"], "season": {1: 1.2, 2: 1.2}},
            {"category": "leisure_culture", "monthly": 330, "count": (3, 6), "merchants": ["Kinepolis", "Decathlon", "Bol.com", "Planckendael", "Zwembad Geerdegem"], "season": {12: 1.5, 7: 1.2}, "card_share": 0.5},
            {"category": "restaurants", "monthly": 250, "count": (3, 6), "merchants": ["Frituur 't Hoekske", "Pizza Hut", "Brasserie Den Grooten Wolsack", "Deliveroo"], "season": {12: 1.3, 7: 0.6}, "card_share": 0.6},
            {"category": "clothing", "monthly": 290, "count": (2, 4), "merchants": ["Zalando", "JBC", "H&M", "Torfs"], "season": {**SALES, 9: 1.6}, "card_share": 0.7},
            {"category": "household_maintenance", "monthly": 280, "count": (2, 5), "merchants": ["Gamma", "IKEA", "Action", "Hubo", "Coolblue"], "season": {4: 1.4, 5: 1.3}, "card_share": 0.4},
            {"category": "other", "monthly": 200, "count": (2, 4), "merchants": ["Kapper", "Cadeaus", "Bpost", "Verjaardagsfeest"], "season": {12: 2.4}},
        ],
        "one_offs": [
            {"date": "2024-11-19", "merchant": "Zalando", "category": "clothing", "amount": -189.95, "account": "BE002-CC"},
            {"date": "2024-11-30", "merchant": "Zalando retour", "category": "clothing", "amount": 189.95, "type": "refund", "account": "BE002-CC"},
            {"date": "2024-12-05", "merchant": "Sinterklaas - Dreamland", "category": "other", "amount": -310, "account": "BE002-CC"},
            {"date": "2025-02-17", "merchant": "Coolblue - wasmachine", "category": "household_maintenance", "amount": -749, "account": "BE002-CC"},
            {"date": "2025-07-08", "merchant": "Sunweb - zomervakantie Frankrijk", "category": "leisure_culture", "amount": -3450, "account": "BE002-CC"},
            {"date": "2025-07-21", "merchant": "Ziekenfonds terugbetaling", "category": "healthcare", "amount": 184.60, "type": "refund"},
            {"date": "2025-10-13", "merchant": "Garage Van Dyck - onderhoud + banden", "category": "transport", "amount": -920},
            {"date": "2025-12-05", "merchant": "Sinterklaas - Dreamland", "category": "other", "amount": -340, "account": "BE002-CC"},
            {"date": "2026-03-24", "merchant": "Bol.com - laptop kinderen", "category": "leisure_culture", "amount": -629, "account": "BE002-CC"},
            {"date": "2026-04-02", "merchant": "Bol.com retour (defect)", "category": "leisure_culture", "amount": 629, "type": "refund", "account": "BE002-CC"},
            {"date": "2026-07-06", "merchant": "Sunweb - zomervakantie Italië", "category": "leisure_culture", "amount": -3720, "account": "BE002-CC"},
            {"date": "2026-09-18", "merchant": "Tandarts Peeters - beugel oudste", "category": "healthcare", "amount": -480},
        ],
        # Scenario: groceries spike in the latest month.
        "overrides": {("2026-09", "food"): {"total": 1420, "count": 19}},
    },
    {
        "id": "BE003",
        "name": "Lucas Peeters",
        "age": 21,
        "profile": "Higher-education student",
        "household": "1 personne (kot)",
        "location": "Leuven, België",
        "income_type": "student job + family support + scholarship",
        "story": "Student living in a kot. Irregular income: parental support, a variable student job (bigger in summer) "
                 "and a yearly scholarship lump sum. Saves summer earnings and draws on savings during the academic year.",
        "accounts": [
            {"id": "BE003-CUR", "type": "current", "name": "Zichtrekening", "opening_balance": 380.00},
            {"id": "BE003-SAV", "type": "savings", "name": "Spaarrekening", "opening_balance": 1200.00},
        ],
        "scheduled": [
            {"kind": "income", "merchant": "Overschrijving ouders", "category": "family_support", "amount": 400, "day": 1},
            {"kind": "income", "merchant": "Studentenjob - Colruyt Leuven", "category": "student_job", "amount": 480, "day": 10, "sd": 0.25,
             "season": {7: 3.0, 8: 3.0, 1: 0.4, 6: 0.4}},
            {"kind": "income", "merchant": "Studietoelage Vlaamse overheid", "category": "scholarship", "amount": 2350, "day": 15, "months": [12], "indexed": True},
            {"kind": "expense", "merchant": "Huur kot - Studentenhuis Naamsestraat", "category": "housing_energy", "amount": 395, "day": 1, "from": "2025-09"},
            {"kind": "expense", "merchant": "Huur kot - Studentenhuis Naamsestraat", "category": "housing_energy", "amount": 375, "day": 1, "to": "2025-08"},
            {"kind": "expense", "merchant": "Kotkosten (energie, internet)", "category": "housing_energy", "amount": 55, "day": 5},
            {"kind": "expense", "merchant": "Mobile Vikings", "category": "communication", "amount": 15, "day": 3},
            {"kind": "expense", "merchant": "Spotify Student", "category": "subscriptions", "amount": 6.99, "day": 12},
            {"kind": "expense", "merchant": "Netflix Basic", "category": "subscriptions", "amount": 9.99, "day": 19},
            {"kind": "expense", "merchant": "Inschrijvingsgeld KU Leuven (beursstudent)", "category": "education", "amount": 125, "day": 4, "months": [10]},
            {"kind": "transfer", "merchant": "Zomerjob sparen", "category": "transfer_to_savings", "amount": 700, "day": 12, "to_account": "BE003-SAV", "months": [7, 8]},
            {"kind": "transfer", "merchant": "Studietoelage sparen", "category": "transfer_to_savings", "amount": 1200, "day": 16, "to_account": "BE003-SAV", "months": [12]},
            {"kind": "transfer", "merchant": "Van spaarrekening", "category": "transfer_from_savings", "amount": 150, "day": 2, "from_account": "BE003-SAV", "months": [2, 3, 4, 5, 6, 10, 11]},
        ],
        "variable": [
            {"category": "food", "monthly": 220, "count": (8, 12), "merchants": ["Aldi", "Lidl", "Colruyt", "Alma studentenrestaurant", "Carrefour Express"], "season": {7: 0.7, 8: 0.7}},
            {"category": "transport", "monthly": 60, "count": (2, 4), "merchants": ["NMBS", "De Lijn", "Velo Leuven", "Blue-bike"], "season": {7: 0.6, 8: 0.6}},
            {"category": "education", "monthly": 35, "count": (1, 2), "merchants": ["Acco cursusdienst", "Standaard Boekhandel", "Copy shop"], "season": {9: 3.0, 10: 2.5, 2: 2.0, 7: 0.1, 8: 0.1}},
            {"category": "healthcare", "monthly": 30, "count": (0, 2), "merchants": ["Apotheek Leuven", "Studentengezondheidscentrum"]},
            {"category": "leisure_culture", "monthly": 70, "count": (2, 4), "merchants": ["Steam", "Cinema Kinepolis Leuven", "Café Nachtwacht", "Het Depot"], "season": {7: 1.4}},
            {"category": "restaurants", "monthly": 45, "count": (2, 5), "merchants": ["Frituur Tip-Top", "Domino's", "Uber Eats", "Starbucks Leuven"]},
            {"category": "clothing", "monthly": 25, "count": (0, 2), "merchants": ["Primark", "H&M", "Vinted"], "season": SALES},
            {"category": "household_maintenance", "monthly": 15, "count": (0, 2), "merchants": ["Action", "Kruidvat"]},
        ],
        "one_offs": [
            {"date": "2025-02-26", "merchant": "Rock Werchter ticket", "category": "leisure_culture", "amount": -289},
            {"date": "2025-09-06", "merchant": "Coolblue - laptop", "category": "education", "amount": -899},
            {"date": "2025-09-05", "merchant": "Van spaarrekening (laptop)", "category": "transfer_from_savings", "amount": 700, "type": "internal_transfer", "from_account": "BE003-SAV"},
            {"date": "2025-11-20", "merchant": "Vinted retour", "category": "clothing", "amount": 24.00, "type": "refund"},
            {"date": "2026-02-24", "merchant": "Rock Werchter ticket", "category": "leisure_culture", "amount": -299},
            {"date": "2026-04-10", "merchant": "Erasmus-trip Lissabon (vlucht)", "category": "leisure_culture", "amount": -185},
        ],
        "overrides": {},
    },
]


def generate_profile(p, rng):
    cur = next(a["id"] for a in p["accounts"] if a["type"] == "current")
    sav = next((a["id"] for a in p["accounts"] if a["type"] == "savings"), None)
    card = next((a["id"] for a in p["accounts"] if a["type"] == "credit_card"), None)
    txs = []

    def add(date, account, amount, merchant, category, type_, **extra):
        txs.append({"date": date, "account_id": account, "amount": round(amount, 2),
                    "merchant": merchant, "category": category, "type": type_, **extra})

    def add_transfer(date, src, dst, amount, merchant, category, recurring):
        tid = f"TRF-{p['id']}-{date}-{len(txs)}"
        add(date, src, -amount, merchant, category, "internal_transfer", transfer_id=tid, recurring=recurring)
        add(date, dst, amount, merchant, category, "internal_transfer", transfer_id=tid, recurring=recurring)

    card_balance_prev = next((a["opening_balance"] for a in p["accounts"] if a["type"] == "credit_card"), 0.0)

    for y, m in months():
        key, dim, factor = ym(y, m), calendar.monthrange(y, m)[1], YEAR_FACTOR[y]
        date = lambda d: f"{key}-{min(d, dim):02d}"

        # Credit card: previous month's statement repaid in full on the 5th.
        if card and card_balance_prev < 0:
            add_transfer(date(5), cur, card, -card_balance_prev, "Kredietkaart - maandafrekening", "credit_card_repayment", True)
        card_month_total = 0.0

        for it in p["scheduled"]:
            if not active(it, key, m):
                continue
            amt = it["amount"] * (factor if it.get("indexed") else 1.0) * it.get("season", {}).get(m, 1.0)
            if it.get("sd"):
                amt *= rng.gauss(1, it["sd"])
            if it["kind"] == "transfer":
                src, dst = (it["from_account"], cur) if "from_account" in it else (cur, it["to_account"])
                add_transfer(date(it["day"]), src, dst, round(amt, 2), it["merchant"], it["category"], True)
            else:
                sign = 1 if it["kind"] == "income" else -1
                add(date(it["day"]), cur, sign * amt, it["merchant"], it["category"], it["kind"], recurring=True)

        for v in p["variable"]:
            ov = p["overrides"].get((key, v["category"]))
            if ov:
                total, n = ov["total"], ov["count"]
            else:
                total = v["monthly"] * factor * v.get("season", {}).get(m, 1.0) * rng.gauss(1, v.get("sd", 0.12))
                n = rng.randint(*v["count"])
            if n == 0:
                continue
            weights = [rng.uniform(0.4, 1.6) for _ in range(n)]
            for w in weights:
                amt = round(total * w / sum(weights), 2)
                acct = card if card and rng.random() < v.get("card_share", 0.0) else cur
                if acct == card:
                    card_month_total -= amt
                add(date(rng.randint(1, dim)), acct, -amt, rng.choice(v["merchants"]), v["category"], "expense", recurring=False)

        for o in p["one_offs"]:
            if not o["date"].startswith(key):
                continue
            if o.get("type") == "internal_transfer":
                add_transfer(o["date"], o["from_account"], cur, o["amount"], o["merchant"], o["category"], False)
                continue
            acct = o.get("account", cur)
            if acct == card:
                card_month_total += o["amount"]
            type_ = o.get("type", "expense" if o["amount"] < 0 else "income")
            add(o["date"], acct, o["amount"], o["merchant"], o["category"], type_, recurring=False, one_off=True)

        # Yearly savings interest (base + fidelity premium) paid early January.
        if sav and m == 1:
            bal = sum(a["opening_balance"] for a in p["accounts"] if a["id"] == sav) + sum(
                t["amount"] for t in txs if t["account_id"] == sav)
            add(date(2), sav, bal * 0.0125, "Intrest spaarrekening", "interest", "income", recurring=True)

        card_balance_prev = card_month_total

    txs.sort(key=lambda t: (t["date"], t["account_id"], t["amount"]))
    for i, t in enumerate(txs, 1):
        t["id"] = f"{p['id']}-TX{i:05d}"
    return [{"id": t.pop("id"), **t} for t in txs]


def monthly_summary(p, txs):
    """Per-month rollup. Internal transfers and card repayments are excluded from
    income/spending; card purchases count once (on the card); refunds net against
    their category."""
    balances = {a["id"]: a["opening_balance"] for a in p["accounts"]}
    savings_ids = {a["id"] for a in p["accounts"] if a["type"] == "savings"}
    by_month = defaultdict(list)
    for t in txs:
        by_month[t["date"][:7]].append(t)

    out = []
    for y, m in months():
        key = ym(y, m)
        income = defaultdict(float)
        spending = defaultdict(float)
        to_savings = 0.0
        for t in by_month[key]:
            balances[t["account_id"]] += t["amount"]
            if t["type"] == "income":
                income[t["category"]] += t["amount"]
            elif t["type"] in ("expense", "refund"):
                spending[t["category"]] -= t["amount"]
            elif t["type"] == "internal_transfer" and t["account_id"] in savings_ids:
                to_savings += t["amount"]
        total_in, total_out = sum(income.values()), sum(spending.values())
        out.append({
            "month": key,
            "income_eur": round(total_in, 2),
            "income_by_source_eur": {k: round(v, 2) for k, v in sorted(income.items())},
            "spending_eur": round(total_out, 2),
            "spending_by_category_eur": {k: round(v, 2) for k, v in sorted(spending.items())},
            "net_cashflow_eur": round(total_in - total_out, 2),
            "net_transfer_to_savings_eur": round(to_savings, 2),
            "closing_balances_eur": {k: round(v, 2) for k, v in balances.items()},
        })
    return out


def recurring_payments(p):
    last = ym(*list(months())[-1])
    rows = []
    for it in p["scheduled"]:
        if it.get("to", "9999-99") < last:
            continue
        rows.append({
            "merchant": it["merchant"], "category": it["category"], "kind": it["kind"],
            "amount_eur": it["amount"], "day_of_month": it["day"],
            "frequency": "monthly" if "months" not in it else ("yearly" if len(it["months"]) == 1 else "monthly_except"),
            **({"months": it["months"]} if "months" in it else {}),
            **({"variable_amount": True} if it.get("sd") or it.get("season") else {}),
        })
    return rows


def main():
    rng = random.Random(SEED)
    profiles = []
    for p in PROFILES:
        txs = generate_profile(p, rng)
        profiles.append({
            **{k: p[k] for k in ("id", "name", "age", "profile", "household", "location", "income_type", "story")},
            "accounts": p["accounts"],
            "recurring": recurring_payments(p),
            "monthly_summary": monthly_summary(p, txs),
            "transactions": txs,
        })

    first, last = ym(*START), ym(*list(months())[-1])
    data = {
        "dataset": {
            "country": "Belgique",
            "currency": "EUR",
            "fictional": True,
            "purpose": "Synthetic long-term banking history for the KBC Time Machine prototype.",
            "privacy": "No real person; all names and profiles are fictional.",
            "period": {"from": first, "to": last, "months": N_MONTHS},
            "generated_by": "generate_sim_user_data.py (seed %d)" % SEED,
            "methodology": {
                "expense_reference": "Statbel Household Budget Survey 2024 (category mix); amounts are synthetic.",
                "reference_expense_shares": {
                    "housing_water_gas_electricity": 30.6,
                    "food_non_alcoholic_beverages": 14.0,
                    "transport": 11.7,
                    "leisure_culture": 7.9,
                    "restaurants_hospitality": 7.3,
                    "healthcare": 4.8,
                    "clothing_footwear": 3.7,
                    "household_maintenance": 5.0,
                },
                "income_reference": "Statbel reports an average gross monthly salary of EUR 4,076 for full-time employees in 2022; the incomes below are synthetic.",
                "indexation": "Amounts are 2026 levels; 2024 and 2025 are scaled by 0.95 and 0.975 for indexed income and variable spending.",
                "conventions": {
                    "amount_sign": "Negative = money leaves the account, positive = money enters it.",
                    "transaction_types": {
                        "income": "New money (salary, pension, benefits, interest).",
                        "expense": "Spending. On the credit card account for card purchases.",
                        "refund": "Money returned for an earlier expense; nets against its category.",
                        "internal_transfer": "Movement between the customer's own accounts (two legs sharing transfer_id). Not income, not spending.",
                    },
                    "credit_card": "Card purchases are recorded on the card account; the full statement is repaid on the 5th of the next month via an internal_transfer (category credit_card_repayment). Count purchases once, never the repayment.",
                    "monthly_summary": "income_eur and spending_eur exclude internal transfers; spending is net of refunds.",
                },
            },
        },
        "profiles": profiles,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    for p in profiles:
        print(f"{p['id']}: {len(p['transactions'])} transactions")


if __name__ == "__main__":
    main()
