#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraveSheet - invulbare D&D character sheets (5e-stijl).
Rekent modifiers, proficiencybonus, redding worpen en vaardigheden
automatisch uit. Meerdere personages, lokaal opgeslagen als .json.
Dravenlock-huisstijl, grote tekst, werkt offline.
"""
import os
import re
import sys
import json

try:
    import pymupdf as _fitz
except Exception:
    try:
        import fitz as _fitz
    except Exception:
        _fitz = None

from PyQt6.QtCore import Qt, QLocale, QUrl
from PyQt6.QtGui import (QPixmap, QIcon, QDesktopServices, QKeySequence,
                         QShortcut)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QComboBox, QLineEdit, QListWidget,
    QListWidgetItem, QPlainTextEdit, QSpinBox, QCheckBox, QScrollArea,
    QFileDialog, QMessageBox, QDialog, QFrame, QStatusBar, QToolButton,
    QSplitter, QSizePolicy)

APP_NAME = "DraveSheet"
APP_VERSION = "0.4.1"
DONATE_URL = "https://paypal.me/roger076"
SUPPORT_MAIL = "service@dravenlock.nl"

BG = "#0e0e11"
PANEL = "#16161b"
SILVER = "#d4d4d4"
MUTE = "#8a8a94"
ACCENT = "#6fa3d6"
WARN = "#e0a23a"

# (sleutel, NL, EN)
ABILITIES = [
    ("str", "Kracht", "Strength"),
    ("dex", "Behendigheid", "Dexterity"),
    ("con", "Constitutie", "Constitution"),
    ("int", "Intelligentie", "Intelligence"),
    ("wis", "Wijsheid", "Wisdom"),
    ("cha", "Charisma", "Charisma"),
]
# (sleutel, NL, EN, eigenschap)
SKILLS = [
    ("atletiek", "Atletiek", "Athletics", "str"),
    ("acrobatiek", "Acrobatiek", "Acrobatics", "dex"),
    ("vingervlugheid", "Vingervlugheid", "Sleight of Hand", "dex"),
    ("heimelijkheid", "Heimelijkheid", "Stealth", "dex"),
    ("arcana", "Arcana", "Arcana", "int"),
    ("geschiedenis", "Geschiedenis", "History", "int"),
    ("onderzoek", "Onderzoek", "Investigation", "int"),
    ("natuur", "Natuur", "Nature", "int"),
    ("religie", "Religie", "Religion", "int"),
    ("dieren", "Dieren verzorgen", "Animal Handling", "wis"),
    ("inzicht", "Inzicht", "Insight", "wis"),
    ("geneeskunde", "Geneeskunde", "Medicine", "wis"),
    ("waarneming", "Waarneming", "Perception", "wis"),
    ("overleven", "Overleven", "Survival", "wis"),
    ("bedrog", "Bedrog", "Deception", "cha"),
    ("intimidatie", "Intimidatie", "Intimidation", "cha"),
    ("optreden", "Optreden", "Performance", "cha"),
    ("overtuiging", "Overtuigingskracht", "Persuasion", "cha"),
]


def ability_mod(score):
    return (int(score) - 10) // 2


def prof_bonus(level):
    return 2 + (max(1, min(20, int(level))) - 1) // 4


def fmt_mod(m):
    return ("+%d" % m) if m >= 0 else ("%d" % m)


# ---------------------------------------------------------------------------
# Pad-/config-helpers
# ---------------------------------------------------------------------------
def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_app_dir(), "dravesheet_config.json")


def _default_folder():
    return os.path.join(_app_dir(), "personages")


DEFAULT_CONFIG = {"lang": "", "folder": "", "pdf_template": ""}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Diagnose-logboek (tijdelijk, om "leeg na opslaan" te vinden)
# ---------------------------------------------------------------------------
DEBUG = False


def _dbg(msg):
    if not DEBUG:
        return
    try:
        import time
        with open(os.path.join(_app_dir(), "dravesheet-debug.txt"),
                  "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + msg + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Taal
# ---------------------------------------------------------------------------
_LANG = "nl"

TRANSLATIONS = {
    "en": {
        "Nieuw personage": "New character", "Opslaan": "Save",
        "Verwijderen": "Delete", "Map kiezen\u2026": "Choose folder\u2026",
        "Zoeken\u2026": "Search\u2026", "Instellingen\u2026": "Settings\u2026",
        "Snelgids": "Quick guide", "Over": "About", "Sluiten": "Close",
        "Taal:": "Language:", "Automatisch (OS)": "Automatic (OS)",
        "Nederlands": "Dutch", "Engels": "English", "Donatie": "Donate",
        "Identiteit": "Identity", "Naam": "Name", "Klasse": "Class",
        "Niveau": "Level", "Ras": "Race", "Achtergrond": "Background",
        "Alignment": "Alignment", "Speler": "Player", "Ervaring": "Experience",
        "Eigenschappen": "Abilities", "Redding": "Save",
        "Vaardigheden": "Skills", "Strijd": "Combat",
        "Wapenrusting (AC)": "Armor Class (AC)", "Initiatief": "Initiative",
        "Snelheid": "Speed", "Proficiencybonus": "Proficiency bonus",
        "Passieve waarneming": "Passive perception",
        "Max HP": "Max HP", "Huidige HP": "Current HP", "Tijdelijke HP": "Temp HP",
        "Hit Dice": "Hit Dice", "Aanvallen": "Attacks & spellcasting",
        "naam": "name", "bonus": "bonus", "schade": "damage",
        "Uitrusting": "Equipment", "Kenmerken & eigenschappen": "Features & traits",
        "Overige vaardigheden & talen": "Other proficiencies & languages",
        "Persoonlijkheid, idealen, banden, gebreken":
            "Personality, ideals, bonds, flaws", "Notities": "Notes",
        "Kies een personage of maak een nieuw.":
            "Pick a character or create a new one.",
        "Nog geen personages. Klik 'Nieuw personage'.":
            "No characters yet. Click 'New character'.",
        "Naamloos": "Unnamed", "personages": "characters", "personage": "character",
        "Niet-opgeslagen wijzigingen": "Unsaved changes",
        "Wil je de wijzigingen opslaan?": "Do you want to save your changes?",
        "Personage verwijderen?": "Delete character?",
        "Weet je zeker dat je dit personage wilt verwijderen?":
            "Are you sure you want to delete this character?",
        "Geef het personage eerst een naam.":
            "Give the character a name first.",
        "snelgids_titel": "DraveSheet - quick guide",
        "Eig.": "Abil.",
        "Exporteren naar PDF\u2026": "Export to PDF\u2026",
        "Kies sjabloon-PDF\u2026": "Choose template PDF\u2026",
        "Kies eerst je eigen blanco invulbare D&D-sheet (PDF).":
            "First choose your own blank fillable D&D sheet (PDF).",
        "PDF opgeslagen:": "PDF saved:", "Nu openen?": "Open it now?",
        "Export mislukt:": "Export failed:",
        "Sheet-PDF (sjabloon):": "Sheet PDF (template):",
        "Kiezen\u2026": "Choose\u2026", "(nog niet gekozen)": "(not chosen yet)",
        "Spreuken": "Spells", "Spreukklasse": "Spellcasting class",
        "Eigenschap": "Ability", "Spell save DC": "Spell save DC",
        "Aanval-bonus": "Attack bonus", "Cantrips": "Cantrips", "Slots:": "Slots:",
        "1 spreuk per regel; * vooraan = paraat":
            "1 spell per line; leading * = prepared",
    }
}


def t(s, lang=None):
    lg = lang or _LANG
    if lg == "nl":
        return s
    return TRANSLATIONS.get(lg, {}).get(s, s)


def ab_name(key, lang=None):
    for k, nl, en in ABILITIES:
        if k == key:
            return nl if (lang or _LANG) == "nl" else en
    return key


def sk_name(skill, lang=None):
    return skill[1] if (lang or _LANG) == "nl" else skill[2]


def detect_lang(cfg):
    forced = (cfg.get("lang") or "").strip().lower()
    if forced in ("nl", "en"):
        return forced
    try:
        if QLocale.system().name().lower().startswith("nl"):
            return "nl"
        return "en"
    except Exception:
        return "nl"


# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------
def _logo_path(name):
    p = os.path.join(_app_dir(), name)
    return p if os.path.exists(p) else None


def logo_pixmap(size=32):
    p = _logo_path("logo.png")
    if p:
        pm = QPixmap(p)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    return pm


def app_icon():
    for n in ("logo.ico", "logo.png"):
        p = _logo_path(n)
        if p:
            ic = QIcon(p)
            if not ic.isNull():
                return ic
    return QIcon()


def slugify(name):
    s = (name or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s]+", "-", s).strip("-")
    return s or "naamloos"


# ---------------------------------------------------------------------------
# Export naar een (eigen) invulbare D&D 5e-PDF
# ---------------------------------------------------------------------------
# Vaardigheidssleutel (DraveSheet) -> genormaliseerde PDF-veldnaam
_SKILL_PDF = {
    "atletiek": "athletics", "acrobatiek": "acrobatics",
    "vingervlugheid": "sleightofhand", "heimelijkheid": "stealth",
    "arcana": "arcana", "geschiedenis": "history", "onderzoek": "investigation",
    "natuur": "nature", "religie": "religion", "dieren": "animal",
    "inzicht": "insight", "geneeskunde": "medicine", "waarneming": "perception",
    "overleven": "survival", "bedrog": "deception", "intimidatie": "intimidation",
    "optreden": "performance", "overtuiging": "persuasion",
}
_SAVE_PDF = {"str": "ststrength", "dex": "stdexterity", "con": "stconstitution",
             "int": "stintelligence", "wis": "stwisdom", "cha": "stcharisma"}


def _norm(s):
    return "".join((s or "").split()).lower()


def _on_state(w):
    try:
        states = w.button_states() or {}
        for k in ("normal", "down"):
            for s in states.get(k, []) or []:
                if s and s != "Off":
                    return s
    except Exception:
        pass
    return "Yes"


def _spell_layout(page):
    """Clustert de spreukvelden van de (volledige) spell-pagina per niveau,
    puur op positie (robuust tegen cryptische namen). Geeft:
    slots[lv1..9]=veldnaam, spells[lv0..9]=geordende veldnamen,
    prepared[spelveld]=checkbox-naam-of-None."""
    ws = list(page.widgets() or [])
    slots_w = [w for w in ws if w.field_name.startswith("SlotsTotal")]
    spell_w = [w for w in ws if w.field_name.startswith("Spells")]
    checks = [(w.field_name, w.rect) for w in ws
              if w.field_type == _fitz.PDF_WIDGET_TYPE_CHECKBOX]
    if not slots_w or not spell_w:
        return None

    def col(x):
        return 0 if x < 210 else (1 if x < 410 else 2)

    slots_sorted = sorted(slots_w, key=lambda w: (col(w.rect.x0), w.rect.y0))
    slots = {}
    heads = []   # (col, y, level)
    for i, w in enumerate(slots_sorted):
        lv = i + 1
        slots[lv] = w.field_name
        heads.append((col(w.rect.x0), w.rect.y0, lv))
    first_col0 = min((y for c, y, _l in heads if c == 0), default=300)

    def level_of(w):
        c = col(w.rect.x0)
        y = w.rect.y0
        if c == 0 and y < first_col0 - 4:
            return 0
        best = None
        for hc, hy, lv in heads:
            if hc == c and y >= hy - 4:
                if best is None or hy > best[0]:
                    best = (hy, lv)
        return best[1] if best else None

    def nearest_check(rect):
        cy = (rect.y0 + rect.y1) / 2
        best, bd = None, 1e9
        for nm, cr in checks:
            if abs((cr.y0 + cr.y1) / 2 - cy) < 5 and cr.x1 <= rect.x0 + 3:
                d = rect.x0 - cr.x1
                if d < bd:
                    bd, best = d, nm
        return best

    spells = {i: [] for i in range(10)}
    prepared = {}
    for w in spell_w:
        lv = level_of(w)
        if lv is None:
            continue
        spells[lv].append(w)
        prepared[w.field_name] = nearest_check(w.rect)
    for lv in spells:
        spells[lv] = [w.field_name for w in
                      sorted(spells[lv], key=lambda w: w.rect.y0)]
    return {"slots": slots, "spells": spells, "prepared": prepared}


def export_character_pdf(template_path, out_path, data):
    """Vult een invulbare D&D 5e-PDF (door de gebruiker aangewezen) met de
    gegevens en bewaart een ingevulde kopie. Geeft (ok, melding)."""
    if _fitz is None:
        return False, "PyMuPDF ontbreekt (pymupdf)."
    try:
        doc = _fitz.open(template_path)
    except Exception as e:
        return False, str(e)

    # afgeleide waarden
    niveau = int(data.get("niveau", 1) or 1)
    prof = prof_bonus(niveau)
    scores = data.get("scores", {})
    save_prof = data.get("save_prof", {})
    skill_prof = data.get("skill_prof", {})
    mods = {k: ability_mod(int(scores.get(k, 10) or 10)) for k, _, _ in ABILITIES}

    vals = {}

    def put(name, value):
        vals[_norm(name)] = "" if value is None else str(value)

    put("CharacterName", data.get("naam", ""))
    put("CharacterName 2", data.get("naam", ""))
    kl = data.get("klasse", "")
    put("ClassLevel", ("%s %s" % (kl, niveau)).strip())
    put("Background", data.get("achtergrond", ""))
    put("PlayerName", data.get("speler", ""))
    put("Race", data.get("ras", ""))
    put("Alignment", data.get("alignment", ""))
    put("XP", data.get("ervaring", ""))
    put("ProfBonus", fmt_mod(prof))
    put("AC", data.get("ac", ""))
    put("Initiative", fmt_mod(mods["dex"]))
    put("Speed", data.get("speed", ""))
    perc_prof = bool(skill_prof.get("waarneming"))
    put("Passive", 10 + mods["wis"] + (prof if perc_prof else 0))
    put("HPMax", data.get("hp_max", ""))
    put("HPCurrent", data.get("hp_cur", ""))
    put("HPTemp", data.get("hp_temp", ""))
    put("HD", data.get("hitdice", ""))
    for k, _, _ in ABILITIES:
        put(k, scores.get(k, ""))
        put(k + "mod", fmt_mod(mods[k]))
        put(_SAVE_PDF[k], fmt_mod(mods[k] + (prof if save_prof.get(k) else 0)))
    for skey, pnorm in _SKILL_PDF.items():
        ab = next(s[3] for s in SKILLS if s[0] == skey)
        val = mods[ab] + (prof if skill_prof.get(skey) else 0)
        vals[pnorm] = fmt_mod(val)
    # aanvallen
    atks = data.get("attacks", [])
    rows = [("Wpn Name", "Wpn1 AtkBonus", "Wpn1 Damage"),
            ("Wpn Name 2", "Wpn2 AtkBonus", "Wpn2 Damage"),
            ("Wpn Name 3", "Wpn3 AtkBonus", "Wpn3 Damage")]
    for i, (nf, bf, df) in enumerate(rows):
        if i < len(atks):
            put(nf, atks[i][0])
            put(bf, atks[i][1])
            put(df, atks[i][2])
    extra = ""
    if len(atks) > 3:
        a = atks[3]
        if any(a):
            extra = "%s  %s  %s" % (a[0], a[1], a[2])
    put("AttacksSpellcasting", extra)
    # tekstvelden
    texts = data.get("texts", {})
    put("Equipment", texts.get("uitrusting", ""))
    put("Features and Traits", texts.get("kenmerken", ""))
    put("ProficienciesLang", texts.get("talen", ""))
    put("PersonalityTraits", texts.get("persoonlijkheid", ""))
    put("Backstory", texts.get("notities", ""))

    # vinkjes (proficiency) -> via positie aan redding/vaardigheid koppelen
    to_check = set()
    try:
        page0 = doc[0]
        ws0 = list(page0.widgets() or [])
        checks = [(w.field_name, w.rect) for w in ws0
                  if w.field_type == _fitz.PDF_WIDGET_TYPE_CHECKBOX]
        textr = {_norm(w.field_name): w.rect for w in ws0
                 if w.field_type == _fitz.PDF_WIDGET_TYPE_TEXT}

        def nearest(rect):
            cy = (rect.y0 + rect.y1) / 2
            best, bd = None, 1e9
            for nm, cr in checks:
                if abs((cr.y0 + cr.y1) / 2 - cy) < 6 and cr.x1 <= rect.x0 + 4:
                    d = rect.x0 - cr.x1
                    if d < bd:
                        bd, best = d, nm
            return best

        for k, _, _ in ABILITIES:
            if save_prof.get(k) and _SAVE_PDF[k] in textr:
                cb = nearest(textr[_SAVE_PDF[k]])
                if cb:
                    to_check.add(cb)
        for skey, pnorm in _SKILL_PDF.items():
            if skill_prof.get(skey) and pnorm in textr:
                cb = nearest(textr[pnorm])
                if cb:
                    to_check.add(cb)
    except Exception:
        pass

    # ---- spreuken (spell-pagina) ----
    spell = data.get("spell", {})
    put("Spellcasting Class 2", spell.get("class", ""))
    put("SpellcastingAbility 2", spell.get("ability", ""))
    put("SpellSaveDC  2", spell.get("dc", ""))
    put("SpellAtkBonus 2", spell.get("atk", ""))
    try:
        lay = None
        for pno in range(doc.page_count):
            lay = _spell_layout(doc[pno])
            if lay:
                break
        if lay:
            slots_data = spell.get("slots", {})
            for lv, fname in lay["slots"].items():
                v = slots_data.get(str(lv), "")
                if v not in ("", 0, "0", None):
                    put(fname, v)
            lists = spell.get("lists", {})
            for lv in range(10):
                text = lists.get(str(lv), "") or ""
                lines = [ln for ln in text.splitlines() if ln.strip()]
                fields = lay["spells"].get(lv, [])
                for i, line in enumerate(lines):
                    if i >= len(fields):
                        break
                    s = line.strip()
                    prep = s.startswith("*")
                    if prep:
                        s = s[1:].strip()
                    put(fields[i], s)
                    if prep and lay["prepared"].get(fields[i]):
                        to_check.add(lay["prepared"][fields[i]])
    except Exception:
        pass

    # invullen
    try:
        for pno in range(doc.page_count):
            page = doc[pno]
            for w in (page.widgets() or []):
                ft = w.field_type
                if ft == _fitz.PDF_WIDGET_TYPE_TEXT:
                    key = _norm(w.field_name)
                    if key in vals and vals[key] != "":
                        w.field_value = vals[key]
                        try:
                            w.text_font = "hebo"   # Helvetica-Bold = vetter
                            h = w.rect.height
                            multiline = bool((w.field_flags or 0) & 4096)
                            if multiline:
                                w.text_fontsize = 12
                            elif h >= 18:
                                w.text_fontsize = 13
                            # kleinere vakjes: auto-grootte (0) laten staan
                        except Exception:
                            pass
                        w.update()
                elif ft == _fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    if w.field_name in to_check:
                        w.field_value = _on_state(w)
                        w.update()
        doc.save(out_path, garbage=4, deflate=True)
        doc.close()
    except Exception as e:
        return False, str(e)
    return True, out_path


# ---------------------------------------------------------------------------
# Snelgids
# ---------------------------------------------------------------------------
GUIDE_NL = """DraveSheet - Snelgids

DraveSheet is een invulbaar D&D-karakterblad (5e-stijl). Het rekent het
meeste automatisch voor je uit, zodat je niet hoeft te rekenen.

Aan de slag
- Klik 'Nieuw personage' en geef het een naam.
- Vul de eigenschappen in (Kracht, Behendigheid, ...). De modifier ernaast
  wordt meteen berekend.
- Zet het niveau goed: de proficiencybonus volgt automatisch.
- Vink aan waar je personage 'proficient' (bedreven) in is bij reddingworpen
  en vaardigheden; de totalen worden direct bijgewerkt.
- Initiatief (uit Behendigheid) en passieve waarneming worden ook vanzelf
  berekend.
- Klik 'Opslaan' (of Ctrl+S).

Spreuken
- Onderaan staat de spreuken-sectie: spreukklasse, eigenschap, save DC en
  aanval-bonus, plus per niveau (cantrips en 1 t/m 9) een vakje. Typ 1 spreuk
  per regel. Zet een * voor de naam om 'paraat' (prepared) aan te geven.
  Vul bij elk niveau het aantal slots in.

Exporteren naar PDF
- Met 'Exporteren naar PDF' vul je je eigen blanco invulbare D&D-sheet
  (PDF) met dit personage. De eerste keer wijs je dat PDF-bestand aan;
  daarna wordt het onthouden (te wijzigen via Instellingen). Modifiers,
  reddingen, vaardigheden en de aangevinkte 'proficiencies' komen er
  automatisch in. Handig om uit te printen of door te sturen.

Meerdere personages
- Links staat de lijst. Klik 'Nieuw personage' voor nog een, of kies er een
  om te bewerken. Zoek bovenin op naam.
- Alles wordt lokaal opgeslagen als .json in je personages-map. Met
  'Map kiezen' kun je een andere map gebruiken (bijv. per campagne of speler).

Tips
- De velden voor uitrusting, kenmerken en notities zijn vrije tekst.
- Je kunt je personages veilig back-uppen door de map te kopieren.

Vragen of een tip? service@dravenlock.nl
"""

GUIDE_EN = """DraveSheet - Quick guide

DraveSheet is a fillable D&D character sheet (5e style). It does most of the
maths for you, so you don't have to calculate.

Getting started
- Click 'New character' and give it a name.
- Fill in the abilities (Strength, Dexterity, ...). The modifier next to it
  is calculated instantly.
- Set the level: the proficiency bonus follows automatically.
- Tick what your character is proficient in for saving throws and skills;
  the totals update right away.
- Initiative (from Dexterity) and passive perception are also auto-calculated.
- Click 'Save' (or Ctrl+S).

Spells
- The spells section is at the bottom: spellcasting class, ability, save DC
  and attack bonus, plus a box per level (cantrips and 1 to 9). Type one spell
  per line. Put a * in front of the name to mark it 'prepared'. Set the number
  of slots per level.

Export to PDF
- 'Export to PDF' fills your own blank fillable D&D sheet (PDF) with this
  character. The first time you point to that PDF; it is then remembered
  (changeable in Settings). Modifiers, saves, skills and the ticked
  proficiencies are filled in automatically. Handy to print or share.

Multiple characters
- The list is on the left. Click 'New character' for another, or pick one to
  edit. Search by name at the top.
- Everything is stored locally as .json in your characters folder. Use
  'Choose folder' for a different folder (e.g. per campaign or player).

Tips
- Equipment, features and notes fields are free text.
- Back up your characters safely by copying the folder.

Questions or feedback? service@dravenlock.nl
"""


class GuideDialog(QDialog):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.setWindowTitle(t("snelgids_titel", lang))
        self.resize(580, 560)
        lay = QVBoxLayout(self)
        from PyQt6.QtWidgets import QTextBrowser
        box = QTextBrowser()
        box.setPlainText(GUIDE_NL if lang == "nl" else GUIDE_EN)
        box.setObjectName("guide")
        lay.addWidget(box)
        row = QHBoxLayout()
        donate = QPushButton("\u2665 " + t("Donatie", lang))
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        row.addWidget(donate)
        row.addStretch(1)
        close = QPushButton(t("Sluiten", lang))
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)


class SettingsDialog(QDialog):
    def __init__(self, parent, cfg, lang):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle(t("Instellingen\u2026", lang))
        self.resize(480, 300)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(t("Taal:", lang)))
        self.langbox = QComboBox()
        self.langbox.addItem(t("Automatisch (OS)", lang), "")
        self.langbox.addItem(t("Nederlands", lang), "nl")
        self.langbox.addItem(t("Engels", lang), "en")
        self.langbox.setCurrentIndex(
            {"": 0, "nl": 1, "en": 2}.get(cfg.get("lang", ""), 0))
        lay.addWidget(self.langbox)

        lay.addSpacing(6)
        lay.addWidget(QLabel(t("Sheet-PDF (sjabloon):", lang)))
        trow = QHBoxLayout()
        self.tpl_lbl = QLabel(cfg.get("pdf_template")
                              or t("(nog niet gekozen)", lang))
        self.tpl_lbl.setObjectName("hint")
        self.tpl_lbl.setWordWrap(True)
        trow.addWidget(self.tpl_lbl, 1)
        pick = QPushButton(t("Kiezen\u2026", lang))
        pick.clicked.connect(self._pick_tpl)
        trow.addWidget(pick)
        lay.addLayout(trow)

        hint = QLabel(t("Sommige instellingen gaan pas in na herstarten.", lang)
                      if lang == "nl" else "Some settings apply after a restart.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        lay.addLayout(row)

    def _pick_tpl(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("Kies sjabloon-PDF\u2026", _LANG), "", "PDF (*.pdf)")
        if path:
            self.cfg["pdf_template"] = path
            self.tpl_lbl.setText(path)

    def result_cfg(self):
        self.cfg["lang"] = self.langbox.currentData()
        return self.cfg


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class DraveSheet(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.lang = _LANG
        self.folder = cfg.get("folder") or _default_folder()
        self.chars = []          # lijst van (slug, naam, path)
        self.cur_slug = None
        self.dirty = False
        self._loading = False

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(1180, 760)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header())
        outer.addWidget(self._toolbar())

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._sidebar())
        split.addWidget(self._sheet_area())
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([300, 880])
        outer.addWidget(split, 1)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self.count_lbl = QLabel("")
        self.count_lbl.setObjectName("muted")
        sb.addWidget(self.count_lbl)
        sb.addPermanentWidget(QLabel("v" + APP_VERSION))
        donate = QToolButton()
        donate.setText("\u2665 " + t("Donatie", self.lang))
        donate.setObjectName("donate")
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        sb.addPermanentWidget(donate)

        QShortcut(QKeySequence("Ctrl+S"), self, self.save_char)
        QShortcut(QKeySequence("Ctrl+N"), self, self.new_char)

        self._ensure_folder()
        self.reload(select_first=True)

    # ---- header / toolbar ----
    def _header(self):
        w = QWidget()
        w.setObjectName("header")
        w.setFixedHeight(54)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(14, 8, 14, 8)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(32))
        lay.addWidget(logo)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        lay.addWidget(title)
        ver = QLabel("v" + APP_VERSION)
        ver.setObjectName("ver")
        lay.addWidget(ver)
        lay.addStretch(1)
        for label, slot in [(t("Instellingen\u2026", self.lang), self._settings),
                            (t("Snelgids", self.lang), self._guide),
                            (t("Over", self.lang), self._about)]:
            b = QPushButton(label)
            b.setObjectName("headerbtn")
            b.clicked.connect(lambda _=False, s=slot: s())
            lay.addWidget(b)
        return w

    def _toolbar(self):
        w = QWidget()
        w.setObjectName("toolbar")
        w.setFixedHeight(50)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(8)
        self.b_new = QPushButton("\u002b  " + t("Nieuw personage", self.lang))
        self.b_new.setObjectName("primary")
        self.b_new.clicked.connect(self.new_char)
        lay.addWidget(self.b_new)
        self.b_save = QPushButton(t("Opslaan", self.lang))
        self.b_save.clicked.connect(self.save_char)
        lay.addWidget(self.b_save)
        self.b_del = QPushButton(t("Verwijderen", self.lang))
        self.b_del.clicked.connect(self.delete_char)
        lay.addWidget(self.b_del)
        lay.addWidget(self._sep())
        self.b_folder = QPushButton("\U0001f4c1  " + t("Map kiezen\u2026", self.lang))
        self.b_folder.clicked.connect(self.choose_folder)
        lay.addWidget(self.b_folder)
        self.b_export = QPushButton("\U0001f4c4  " + t("Exporteren naar PDF\u2026", self.lang))
        self.b_export.clicked.connect(self._export_pdf)
        lay.addWidget(self.b_export)
        lay.addStretch(1)
        return w

    def _sidebar(self):
        w = QWidget()
        w.setObjectName("sidebar")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText(t("Zoeken\u2026", self.lang))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._refresh_list)
        lay.addWidget(self.search)
        self.listw = QListWidget()
        self.listw.setObjectName("charlist")
        self.listw.currentItemChanged.connect(self._on_select)
        lay.addWidget(self.listw, 1)
        return w

    def _sep(self):
        s = QFrame()
        s.setFrameShape(QFrame.Shape.VLine)
        s.setObjectName("sep")
        return s

    # ---- het blad zelf ----
    def _sheet_area(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("sheetscroll")
        self.sheet = QWidget()
        self.sheet.setObjectName("sheet")
        v = QVBoxLayout(self.sheet)
        v.setContentsMargins(16, 14, 16, 16)
        v.setSpacing(14)

        self.idf = {}
        self.ab_score = {}
        self.ab_mod = {}
        self.save_prof = {}
        self.save_val = {}
        self.sk_prof = {}
        self.sk_val = {}
        self.atk = []
        self.txt = {}
        self.spell_hdr = {}
        self.spell_slots = {}
        self.spell_text = {}

        v.addWidget(self._sec_identity())
        midrow = QHBoxLayout()
        midrow.setSpacing(14)
        leftcol = QVBoxLayout()
        leftcol.setSpacing(14)
        leftcol.addWidget(self._sec_abilities())
        leftcol.addWidget(self._sec_combat())
        rightcol = QVBoxLayout()
        rightcol.setSpacing(14)
        rightcol.addWidget(self._sec_skills())
        lw = QWidget()
        lw.setLayout(leftcol)
        rw = QWidget()
        rw.setLayout(rightcol)
        midrow.addWidget(lw, 1)
        midrow.addWidget(rw, 1)
        mid = QWidget()
        mid.setLayout(midrow)
        v.addWidget(mid)
        v.addWidget(self._sec_attacks())
        v.addWidget(self._sec_texts())
        v.addWidget(self._sec_spells())
        v.addStretch(1)

        self.scroll.setWidget(self.sheet)
        return self.scroll

    def _card(self, title):
        box = QWidget()
        box.setObjectName("card")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)
        lab = QLabel(title)
        lab.setObjectName("cardtitle")
        lay.addWidget(lab)
        return box, lay

    def _line(self, key, store):
        e = QLineEdit()
        e.textEdited.connect(self._mark_dirty)
        store[key] = e
        return e

    def _sec_identity(self):
        box, lay = self._card(t("Identiteit", self.lang))
        g = QGridLayout()
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(8)
        fields1 = [("naam", t("Naam", self.lang)),
                   ("klasse", t("Klasse", self.lang)),
                   ("ras", t("Ras", self.lang)),
                   ("achtergrond", t("Achtergrond", self.lang))]
        fields2 = [("alignment", t("Alignment", self.lang)),
                   ("speler", t("Speler", self.lang)),
                   ("ervaring", t("Ervaring", self.lang))]
        r = 0
        for key, label in fields1:
            g.addWidget(self._mklabel(label), r, 0)
            g.addWidget(self._line(key, self.idf), r, 1)
            r += 1
        # niveau als spinbox
        g.addWidget(self._mklabel(t("Niveau", self.lang)), 0, 2)
        self.level = QSpinBox()
        self.level.setRange(1, 20)
        self.level.setValue(1)
        self.level.valueChanged.connect(self._on_calc_change)
        g.addWidget(self.level, 0, 3)
        r2 = 1
        for key, label in fields2:
            g.addWidget(self._mklabel(label), r2, 2)
            g.addWidget(self._line(key, self.idf), r2, 3)
            r2 += 1
        g.setColumnStretch(1, 1)
        g.setColumnStretch(3, 1)
        lay.addLayout(g)
        return box

    def _mklabel(self, text):
        l = QLabel(text)
        l.setObjectName("flabel")
        return l

    def _sec_abilities(self):
        box, lay = self._card(t("Eigenschappen", self.lang))
        g = QGridLayout()
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.addWidget(self._mklabel(t("Eig.", self.lang)), 0, 0)
        g.addWidget(self._mklabel("Score"), 0, 1)
        g.addWidget(self._mklabel("Mod"), 0, 2)
        g.addWidget(self._mklabel(t("Redding", self.lang)), 0, 3, 1, 2)
        row = 1
        for key, nl, en in ABILITIES:
            g.addWidget(self._mklabel(ab_name(key, self.lang)), row, 0)
            sp = QSpinBox()
            sp.setRange(1, 30)
            sp.setValue(10)
            sp.valueChanged.connect(self._on_calc_change)
            self.ab_score[key] = sp
            g.addWidget(sp, row, 1)
            md = QLabel("+0")
            md.setObjectName("calc")
            md.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ab_mod[key] = md
            g.addWidget(md, row, 2)
            cb = QCheckBox()
            cb.toggled.connect(self._on_calc_change)
            self.save_prof[key] = cb
            g.addWidget(cb, row, 3)
            sv = QLabel("+0")
            sv.setObjectName("calc")
            sv.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.save_val[key] = sv
            g.addWidget(sv, row, 4)
            row += 1
        g.setColumnStretch(0, 1)
        lay.addLayout(g)
        return box

    def _sec_skills(self):
        box, lay = self._card(t("Vaardigheden", self.lang))
        g = QGridLayout()
        g.setHorizontalSpacing(8)
        g.setVerticalSpacing(5)
        row = 0
        for skill in SKILLS:
            key = skill[0]
            cb = QCheckBox()
            cb.toggled.connect(self._on_calc_change)
            self.sk_prof[key] = cb
            g.addWidget(cb, row, 0)
            val = QLabel("+0")
            val.setObjectName("calc")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sk_val[key] = val
            g.addWidget(val, row, 1)
            name = QLabel("%s  (%s)" % (sk_name(skill, self.lang),
                                        skill[3].upper()))
            g.addWidget(name, row, 2)
            row += 1
        g.setColumnStretch(2, 1)
        lay.addLayout(g)
        return box

    def _sec_combat(self):
        box, lay = self._card(t("Strijd", self.lang))
        g = QGridLayout()
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        self.ac = QSpinBox()
        self.ac.setRange(0, 40)
        self.ac.setValue(10)
        self.ac.valueChanged.connect(self._mark_dirty)
        self.speed = QLineEdit("30")
        self.speed.textEdited.connect(self._mark_dirty)
        self.hp_max = QSpinBox()
        self.hp_max.setRange(0, 999)
        self.hp_max.valueChanged.connect(self._mark_dirty)
        self.hp_cur = QSpinBox()
        self.hp_cur.setRange(-99, 999)
        self.hp_cur.valueChanged.connect(self._mark_dirty)
        self.hp_temp = QSpinBox()
        self.hp_temp.setRange(0, 999)
        self.hp_temp.valueChanged.connect(self._mark_dirty)
        self.hitdice = QLineEdit()
        self.hitdice.textEdited.connect(self._mark_dirty)
        self.init_val = QLabel("+0")
        self.init_val.setObjectName("calc")
        self.prof_val = QLabel("+2")
        self.prof_val.setObjectName("calc")
        self.passive_val = QLabel("10")
        self.passive_val.setObjectName("calc")

        rows = [
            (t("Wapenrusting (AC)", self.lang), self.ac),
            (t("Initiatief", self.lang), self.init_val),
            (t("Snelheid", self.lang), self.speed),
            (t("Proficiencybonus", self.lang), self.prof_val),
            (t("Passieve waarneming", self.lang), self.passive_val),
            (t("Max HP", self.lang), self.hp_max),
            (t("Huidige HP", self.lang), self.hp_cur),
            (t("Tijdelijke HP", self.lang), self.hp_temp),
            (t("Hit Dice", self.lang), self.hitdice),
        ]
        r = 0
        for label, widget in rows:
            g.addWidget(self._mklabel(label), r, 0)
            g.addWidget(widget, r, 1)
            r += 1
        g.setColumnStretch(0, 1)
        lay.addLayout(g)
        return box

    def _sec_attacks(self):
        box, lay = self._card(t("Aanvallen", self.lang))
        g = QGridLayout()
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(6)
        g.addWidget(self._mklabel(t("naam", self.lang)), 0, 0)
        g.addWidget(self._mklabel(t("bonus", self.lang)), 0, 1)
        g.addWidget(self._mklabel(t("schade", self.lang)), 0, 2)
        for i in range(4):
            n = QLineEdit()
            b = QLineEdit()
            d = QLineEdit()
            for e in (n, b, d):
                e.textEdited.connect(self._mark_dirty)
            self.atk.append((n, b, d))
            g.addWidget(n, i + 1, 0)
            g.addWidget(b, i + 1, 1)
            g.addWidget(d, i + 1, 2)
        g.setColumnStretch(0, 3)
        g.setColumnStretch(1, 1)
        g.setColumnStretch(2, 2)
        lay.addLayout(g)
        return box

    def _sec_texts(self):
        box, lay = self._card("")
        keys = [("uitrusting", t("Uitrusting", self.lang)),
                ("kenmerken", t("Kenmerken & eigenschappen", self.lang)),
                ("talen", t("Overige vaardigheden & talen", self.lang)),
                ("persoonlijkheid",
                 t("Persoonlijkheid, idealen, banden, gebreken", self.lang)),
                ("notities", t("Notities", self.lang))]
        for key, label in keys:
            lb = QLabel(label)
            lb.setObjectName("flabel")
            lay.addWidget(lb)
            te = QPlainTextEdit()
            te.setObjectName("bigtext")
            te.setMinimumHeight(70)
            te.textChanged.connect(self._mark_dirty)
            self.txt[key] = te
            lay.addWidget(te)
        return box

    def _sec_spells(self):
        box, lay = self._card(t("Spreuken", self.lang))
        hdr = QGridLayout()
        hdr.setHorizontalSpacing(12)
        hdr.setVerticalSpacing(8)
        specs = [("class", t("Spreukklasse", self.lang)),
                 ("ability", t("Eigenschap", self.lang)),
                 ("dc", t("Spell save DC", self.lang)),
                 ("atk", t("Aanval-bonus", self.lang))]
        for i, (key, label) in enumerate(specs):
            hdr.addWidget(self._mklabel(label), 0, i)
            e = QLineEdit()
            e.textEdited.connect(self._mark_dirty)
            self.spell_hdr[key] = e
            hdr.addWidget(e, 1, i)
            hdr.setColumnStretch(i, 1)
        lay.addLayout(hdr)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        for idx, lv in enumerate(range(0, 10)):
            cell = QWidget()
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(4)
            hrow = QHBoxLayout()
            name = t("Cantrips", self.lang) if lv == 0 else \
                "%s %d" % (t("Niveau", self.lang), lv)
            lb = QLabel(name)
            lb.setObjectName("flabel")
            hrow.addWidget(lb)
            hrow.addStretch(1)
            if lv >= 1:
                hrow.addWidget(QLabel(t("Slots:", self.lang)))
                sp = QSpinBox()
                sp.setRange(0, 9)
                sp.valueChanged.connect(self._mark_dirty)
                self.spell_slots[lv] = sp
                hrow.addWidget(sp)
            cl.addLayout(hrow)
            te = QPlainTextEdit()
            te.setObjectName("bigtext")
            te.setMinimumHeight(66)
            if lv == 0:
                te.setPlaceholderText("1 cantrip per regel")
            else:
                te.setPlaceholderText(t("1 spreuk per regel; * vooraan = paraat",
                                        self.lang))
            te.textChanged.connect(self._mark_dirty)
            self.spell_text[lv] = te
            cl.addWidget(te)
            grid.addWidget(cell, idx // 2, idx % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)
        return box

    # ---- berekeningen ----
    def _on_calc_change(self, *_):
        self._recalc()
        self._mark_dirty()

    def _recalc(self):
        prof = prof_bonus(self.level.value())
        self.prof_val.setText(fmt_mod(prof))
        mods = {}
        for key, _nl, _en in ABILITIES:
            m = ability_mod(self.ab_score[key].value())
            mods[key] = m
            self.ab_mod[key].setText(fmt_mod(m))
            sv = m + (prof if self.save_prof[key].isChecked() else 0)
            self.save_val[key].setText(fmt_mod(sv))
        self.init_val.setText(fmt_mod(mods["dex"]))
        perc_prof = self.sk_prof["waarneming"].isChecked()
        self.passive_val.setText(str(10 + mods["wis"] + (prof if perc_prof else 0)))
        for skill in SKILLS:
            key = skill[0]
            ab = skill[3]
            val = mods[ab] + (prof if self.sk_prof[key].isChecked() else 0)
            self.sk_val[key].setText(fmt_mod(val))

    # ---- gegevens <-> widgets ----
    def gather(self):
        d = {"versie": 1}
        for k, e in self.idf.items():
            d[k] = e.text()
        d["niveau"] = self.level.value()
        d["scores"] = {k: self.ab_score[k].value() for k, _, _ in ABILITIES}
        d["save_prof"] = {k: self.save_prof[k].isChecked() for k, _, _ in ABILITIES}
        d["skill_prof"] = {s[0]: self.sk_prof[s[0]].isChecked() for s in SKILLS}
        d["ac"] = self.ac.value()
        d["speed"] = self.speed.text()
        d["hp_max"] = self.hp_max.value()
        d["hp_cur"] = self.hp_cur.value()
        d["hp_temp"] = self.hp_temp.value()
        d["hitdice"] = self.hitdice.text()
        d["attacks"] = [[n.text(), b.text(), dd.text()] for n, b, dd in self.atk]
        d["texts"] = {k: te.toPlainText() for k, te in self.txt.items()}
        d["spell"] = {
            "class": self.spell_hdr["class"].text(),
            "ability": self.spell_hdr["ability"].text(),
            "dc": self.spell_hdr["dc"].text(),
            "atk": self.spell_hdr["atk"].text(),
            "slots": {str(lv): self.spell_slots[lv].value()
                      for lv in self.spell_slots},
            "lists": {str(lv): self.spell_text[lv].toPlainText()
                      for lv in self.spell_text},
        }
        return d

    def apply(self, d):
        _dbg("apply() AANGEROEPEN naam=%r velden=%d _loading=%s"
             % (d.get("naam", ""), len(d), self._loading))
        self._loading = True
        try:
            for k, e in self.idf.items():
                e.setText(str(d.get(k, "")))
            self.level.setValue(int(d.get("niveau", 1) or 1))
            sc = d.get("scores", {})
            for k, _, _ in ABILITIES:
                self.ab_score[k].setValue(int(sc.get(k, 10) or 10))
            sp = d.get("save_prof", {})
            for k, _, _ in ABILITIES:
                self.save_prof[k].setChecked(bool(sp.get(k, False)))
            skp = d.get("skill_prof", {})
            for s in SKILLS:
                self.sk_prof[s[0]].setChecked(bool(skp.get(s[0], False)))
            self.ac.setValue(int(d.get("ac", 10) or 0))
            self.speed.setText(str(d.get("speed", "")))
            self.hp_max.setValue(int(d.get("hp_max", 0) or 0))
            self.hp_cur.setValue(int(d.get("hp_cur", 0) or 0))
            self.hp_temp.setValue(int(d.get("hp_temp", 0) or 0))
            self.hitdice.setText(str(d.get("hitdice", "")))
            atks = d.get("attacks", [])
            for i, (n, b, dd) in enumerate(self.atk):
                row = atks[i] if i < len(atks) else ["", "", ""]
                n.setText(str(row[0] if len(row) > 0 else ""))
                b.setText(str(row[1] if len(row) > 1 else ""))
                dd.setText(str(row[2] if len(row) > 2 else ""))
            tx = d.get("texts", {})
            for k, te in self.txt.items():
                te.setPlainText(str(tx.get(k, "")))
            sp = d.get("spell", {})
            self.spell_hdr["class"].setText(str(sp.get("class", "")))
            self.spell_hdr["ability"].setText(str(sp.get("ability", "")))
            self.spell_hdr["dc"].setText(str(sp.get("dc", "")))
            self.spell_hdr["atk"].setText(str(sp.get("atk", "")))
            slots = sp.get("slots", {})
            for lv, w in self.spell_slots.items():
                w.setValue(int(slots.get(str(lv), 0) or 0))
            lists = sp.get("lists", {})
            for lv, te in self.spell_text.items():
                te.setPlainText(str(lists.get(str(lv), "")))
        finally:
            self._loading = False
        self._recalc()

    def _blank(self):
        _dbg("_blank() -> apply({}) (leegt de sheet)")
        self.apply({})

    # ---- map / lijst ----
    def _ensure_folder(self):
        try:
            os.makedirs(self.folder, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))

    def reload(self, select_first=False, select_slug=None):
        self.chars = []
        try:
            for name in sorted(os.listdir(self.folder)):
                if not name.lower().endswith(".json"):
                    continue
                path = os.path.join(self.folder, name)
                nm = name[:-5]
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    nm = data.get("naam") or nm
                except Exception:
                    pass
                self.chars.append((name[:-5], nm, path))
        except Exception:
            pass
        self._refresh_list()
        if select_slug and self._select_slug(select_slug):
            pass
        elif select_first and self.listw.count():
            self.listw.setCurrentRow(0)
        else:
            self._set_enabled(False)
            self.cur_slug = None
        self._update_count()

    def _rescan_keep(self):
        _dbg("_rescan_keep() start cur_slug=%r" % self.cur_slug)
        return self._rescan_keep_impl()

    def _rescan_keep_impl(self):
        """Herbouwt de personagelijst vanaf schijf en selecteert het huidige
        personage stil in de lijst, ZONDER de velden te herladen. Zo blijven de
        zojuist opgeslagen gegevens gewoon in beeld (geen lege sheet)."""
        self.chars = []
        try:
            for name in sorted(os.listdir(self.folder)):
                if not name.lower().endswith(".json"):
                    continue
                path = os.path.join(self.folder, name)
                nm = name[:-5]
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    nm = data.get("naam") or nm
                except Exception:
                    pass
                self.chars.append((name[:-5], nm, path))
        except Exception:
            pass
        self._refresh_list()
        self._update_count()

    def _refresh_list(self):
        q = (self.search.text() or "").strip().lower()
        self.listw.blockSignals(True)
        keep = self.cur_slug
        self.listw.clear()
        for slug, nm, _path in sorted(self.chars, key=lambda x: x[1].lower()):
            if q and q not in nm.lower():
                continue
            it = QListWidgetItem(nm or t("Naamloos", self.lang))
            it.setData(Qt.ItemDataRole.UserRole, slug)
            self.listw.addItem(it)
        self.listw.blockSignals(False)
        if keep:
            self._select_slug(keep, silent=True)

    def _select_slug(self, slug, silent=False):
        for i in range(self.listw.count()):
            if self.listw.item(i).data(Qt.ItemDataRole.UserRole) == slug:
                if silent:
                    self.listw.blockSignals(True)
                self.listw.setCurrentRow(i)
                if silent:
                    self.listw.blockSignals(False)
                return True
        return False

    def _path_for(self, slug):
        for s, _nm, p in self.chars:
            if s == slug:
                return p
        return os.path.join(self.folder, slug + ".json")

    def _set_enabled(self, on):
        self.sheet.setEnabled(on)
        self.b_save.setEnabled(on)
        self.b_del.setEnabled(on)
        self.b_export.setEnabled(on)

    # ---- selectie ----
    def _on_select(self, cur, _prev):
        _dbg("_on_select cur=%r _loading=%s dirty=%s cur_slug=%r"
             % (cur.data(Qt.ItemDataRole.UserRole) if cur else None,
                self._loading, self.dirty, self.cur_slug))
        if self._loading:
            return
        if not self._maybe_save_changes():
            return
        if cur is None:
            self._set_enabled(False)
            self.cur_slug = None
            return
        slug = cur.data(Qt.ItemDataRole.UserRole)
        self._load_slug(slug)

    def _load_slug(self, slug):
        _dbg("_load_slug(%r)" % slug)
        path = self._path_for(slug)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))
            return
        self.cur_slug = slug
        self._set_enabled(True)
        self.apply(data)
        self.dirty = False
        self._update_title()

    # ---- acties ----
    def _mark_dirty(self, *_):
        if not self._loading:
            self.dirty = True
            self._update_title()

    def _maybe_save_changes(self):
        if self.cur_slug is None or not self.dirty:
            return True
        r = QMessageBox.question(
            self, t("Niet-opgeslagen wijzigingen", self.lang),
            t("Wil je de wijzigingen opslaan?", self.lang),
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel)
        if r == QMessageBox.StandardButton.Save:
            return self.save_char()
        if r == QMessageBox.StandardButton.Cancel:
            return False
        self.dirty = False
        return True

    def new_char(self, *_):
        if not self._maybe_save_changes():
            return
        self.listw.blockSignals(True)
        self.listw.setCurrentRow(-1)
        self.listw.blockSignals(False)
        self.cur_slug = None
        self._set_enabled(True)
        self._blank()
        self.dirty = False
        self.idf["naam"].setFocus()
        self._update_title()

    def save_char(self):
        if not self.sheet.isEnabled():
            return False
        name = self.idf["naam"].text().strip()
        if not name:
            QMessageBox.information(self, APP_NAME,
                                    t("Geef het personage eerst een naam.", self.lang))
            self.idf["naam"].setFocus()
            return False
        data = self.gather()
        _dbg("save_char: naam=%r cur_slug=%r aantal_velden=%d"
             % (name, self.cur_slug, len(data)))
        new_slug = slugify(name)
        existing = {s for s, _n, _p in self.chars if s != self.cur_slug}
        base = new_slug
        n = 2
        while new_slug in existing:
            new_slug = "%s-%d" % (base, n)
            n += 1
        old_slug = self.cur_slug
        path = os.path.join(self.folder, new_slug + ".json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if old_slug and old_slug != new_slug:
                old_path = os.path.join(self.folder, old_slug + ".json")
                if os.path.exists(old_path):
                    os.remove(old_path)
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))
            return False
        self.cur_slug = new_slug
        self.dirty = False
        _dbg("save_char: geschreven naar %r, nu _rescan_keep()" % path)
        self._rescan_keep()
        _dbg("save_char: KLAAR. naam-veld nu=%r" % self.idf["naam"].text())
        self.statusBar().showMessage(t("Opslaan", self.lang) + " \u2713", 2500)
        self._update_title()
        return True

    def delete_char(self):
        if self.cur_slug is None:
            return
        r = QMessageBox.question(
            self, t("Personage verwijderen?", self.lang),
            t("Weet je zeker dat je dit personage wilt verwijderen?", self.lang),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r != QMessageBox.StandardButton.Yes:
            return
        path = self._path_for(self.cur_slug)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))
            return
        self.cur_slug = None
        self.dirty = False
        self.reload(select_first=True)

    def choose_folder(self):
        if not self._maybe_save_changes():
            return
        path = QFileDialog.getExistingDirectory(
            self, t("Map kiezen\u2026", self.lang), self.folder)
        if not path:
            return
        self.folder = path
        self.cfg["folder"] = path
        save_config(self.cfg)
        self.cur_slug = None
        self.dirty = False
        self.reload(select_first=True)

    def _export_pdf(self):
        if not self.sheet.isEnabled():
            return
        name = self.idf["naam"].text().strip()
        if not name:
            QMessageBox.information(
                self, APP_NAME, t("Geef het personage eerst een naam.", self.lang))
            self.idf["naam"].setFocus()
            return
        tpl = self.cfg.get("pdf_template", "")
        if not tpl or not os.path.exists(tpl):
            QMessageBox.information(
                self, APP_NAME,
                t("Kies eerst je eigen blanco invulbare D&D-sheet (PDF).", self.lang))
            tpl, _ = QFileDialog.getOpenFileName(
                self, t("Kies sjabloon-PDF\u2026", self.lang), "", "PDF (*.pdf)")
            if not tpl:
                return
            self.cfg["pdf_template"] = tpl
            save_config(self.cfg)
        out, _ = QFileDialog.getSaveFileName(
            self, t("Exporteren naar PDF\u2026", self.lang),
            slugify(name) + ".pdf", "PDF (*.pdf)")
        if not out:
            return
        if not out.lower().endswith(".pdf"):
            out += ".pdf"
        ok, msg = export_character_pdf(tpl, out, self.gather())
        if ok:
            r = QMessageBox.question(
                self, APP_NAME,
                "%s\n%s\n\n%s" % (t("PDF opgeslagen:", self.lang), out,
                                  t("Nu openen?", self.lang)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if r == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(QUrl.fromLocalFile(out))
        else:
            QMessageBox.warning(
                self, APP_NAME, "%s\n%s" % (t("Export mislukt:", self.lang), msg))

    # ---- diversen ----
    def _update_count(self):
        n = len(self.chars)
        word = t("personage", self.lang) if n == 1 else t("personages", self.lang)
        self.count_lbl.setText("%d %s  \u2014  %s" % (n, word, self.folder))

    def _update_title(self):
        mark = "*" if (self.sheet.isEnabled() and self.dirty) else ""
        name = self.idf["naam"].text().strip() if self.sheet.isEnabled() else ""
        if name:
            self.setWindowTitle("%s \u2014 %s%s" % (APP_NAME, name, mark))
        else:
            self.setWindowTitle(APP_NAME)

    def _settings(self):
        dlg = SettingsDialog(self, dict(self.cfg), self.lang)
        if dlg.exec():
            self.cfg = dlg.result_cfg()
            save_config(self.cfg)

    def _guide(self):
        GuideDialog(self, self.lang).exec()

    def _about(self):
        QMessageBox.information(
            self, t("Over", self.lang),
            "%s v%s\n\nInvulbare D&D character sheets.\nDravenlock\n%s\n%s"
            % (APP_NAME, APP_VERSION, SUPPORT_MAIL, DONATE_URL))

    def closeEvent(self, ev):
        if not self._maybe_save_changes():
            ev.ignore()
            return
        ev.accept()


QSS = """
* { font-family: 'Segoe UI', sans-serif; font-size: 15px; color: %(silver)s; }
QMainWindow, QWidget { background: %(bg)s; }
#header { background: %(panel)s; border-bottom: 1px solid #23232b; }
#title { font-size: 19px; font-weight: 700; }
#ver { color: %(mute)s; font-size: 12px; }
#toolbar { background: %(bg)s; border-bottom: 1px solid #23232b; }
#sidebar { background: %(panel)s; border-right: 1px solid #23232b; }
QScrollArea#sheetscroll { border: none; }
#sheet { background: %(bg)s; }
#card { background: %(panel)s; border: 1px solid #23232b; border-radius: 12px; }
#cardtitle { font-size: 16px; font-weight: 700; color: %(accent)s; }
#flabel { color: %(mute)s; }
#calc { background: #1a1a20; border: 1px solid #2c2c36; border-radius: 6px;
        padding: 4px 6px; font-weight: 700; color: #ffffff; min-width: 38px; }
QPushButton { background: %(panel)s; border: 1px solid #2c2c36; border-radius: 8px;
              padding: 8px 13px; color: %(silver)s; }
QPushButton:hover { border-color: %(accent)s; }
QPushButton:disabled { color: #5a5a63; }
QPushButton#primary { background: %(accent)s; color: #08131f; font-weight: 700;
                      border: none; }
QPushButton#primary:hover { background: #87b6e3; }
QPushButton#headerbtn { padding: 6px 11px; }
QToolButton#donate { border: none; background: transparent; color: %(accent)s; }
QFrame#sep { color: #2c2c36; }
#muted, #hint { color: %(mute)s; font-size: 13px; }
QLineEdit, QComboBox, QPlainTextEdit, QSpinBox {
    background: #1a1a20; border: 1px solid #3a3a46; border-radius: 8px;
    padding: 7px; color: #ffffff; font-size: 16px; font-weight: 600;
    selection-background-color: %(accent)s; selection-color: #08131f; }
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus,
QComboBox:focus { border-color: %(accent)s; }
QPlainTextEdit#bigtext { font-size: 16px; font-weight: 600; }
QListWidget#charlist { background: #1a1a20; border: 1px solid #2c2c36;
    border-radius: 8px; padding: 4px; font-size: 16px; }
QListWidget#charlist::item { padding: 10px 8px; border-radius: 6px; color: %(silver)s; }
QListWidget#charlist::item:selected { background: #26323f; color: #ffffff;
    font-weight: 700; border-left: 3px solid %(accent)s; }
QListWidget#charlist::item:hover { background: #23232c; }
QComboBox QAbstractItemView { background: #1a1a20; color: %(silver)s;
    selection-background-color: %(accent)s; selection-color: #08131f; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid %(accent)s;
    border-radius: 4px; background: #1a1a20; }
QCheckBox::indicator:checked { background: %(accent)s; }
QTextBrowser#guide { background: %(panel)s; border: 1px solid #2c2c36;
                     border-radius: 8px; padding: 10px; }
QStatusBar { background: %(panel)s; }
QSplitter::handle { background: #23232b; }
QDialog { background: %(bg)s; }
""" % {"bg": BG, "panel": PANEL, "silver": SILVER, "mute": MUTE,
       "accent": ACCENT, "warn": WARN}


def _install_excepthook():
    import traceback

    def hook(exctype, value, tb):
        msg = "".join(traceback.format_exception(exctype, value, tb))
        try:
            with open(os.path.join(_app_dir(), "dravesheet-fout.txt"),
                      "w", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
        try:
            if QApplication.instance():
                QMessageBox.critical(None, "DraveSheet - fout",
                                     "Er ging iets mis:\n\n" + msg[-1500:]
                                     + "\n\n(Ook opgeslagen in dravesheet-fout.txt)")
        except Exception:
            pass
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = hook


def main():
    global _LANG
    _install_excepthook()
    app = QApplication(sys.argv)
    try:
        cfg = load_config()
        _LANG = detect_lang(cfg)
        app.setStyleSheet(QSS)
        win = DraveSheet(cfg)
        win.show()
    except Exception:
        sys.excepthook(*sys.exc_info())
        return
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
