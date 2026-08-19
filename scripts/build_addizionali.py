#!/usr/bin/env python3
"""Build docs/addizionali-2025.json from MEF municipal xlsx + regional CSV."""

from __future__ import annotations

import csv
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUNICIPAL = ROOT / "files" / "addizionale-comunale-IRPEF-2025.xlsx"
REGIONAL = ROOT / "files" / "Add_regionale_irpef2025.csv"
OUT = ROOT / "docs" / "addizionali-2025.json"
XLSX_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
PROGRESSIVE_UPPERS = {
    3: [28000.0, 50000.0, None],
    4: [15000.0, 28000.0, 50000.0, None],
}

PROVINCE_TO_REGION = {
    "AQ": "Abruzzo",
    "CH": "Abruzzo",
    "PE": "Abruzzo",
    "TE": "Abruzzo",
    "MT": "Basilicata",
    "PZ": "Basilicata",
    "CZ": "Calabria",
    "CS": "Calabria",
    "KR": "Calabria",
    "RC": "Calabria",
    "VV": "Calabria",
    "AV": "Campania",
    "BN": "Campania",
    "CE": "Campania",
    "NA": "Campania",
    "SA": "Campania",
    "BO": "Emilia-Romagna",
    "FE": "Emilia-Romagna",
    "FC": "Emilia-Romagna",
    "MO": "Emilia-Romagna",
    "PR": "Emilia-Romagna",
    "PC": "Emilia-Romagna",
    "RA": "Emilia-Romagna",
    "RE": "Emilia-Romagna",
    "RN": "Emilia-Romagna",
    "GO": "Friuli-Venezia Giulia",
    "PN": "Friuli-Venezia Giulia",
    "TS": "Friuli-Venezia Giulia",
    "UD": "Friuli-Venezia Giulia",
    "FR": "Lazio",
    "LT": "Lazio",
    "RI": "Lazio",
    "RM": "Lazio",
    "VT": "Lazio",
    "GE": "Liguria",
    "IM": "Liguria",
    "SP": "Liguria",
    "SV": "Liguria",
    "BG": "Lombardia",
    "BS": "Lombardia",
    "CO": "Lombardia",
    "CR": "Lombardia",
    "LC": "Lombardia",
    "LO": "Lombardia",
    "MN": "Lombardia",
    "MI": "Lombardia",
    "MB": "Lombardia",
    "PV": "Lombardia",
    "SO": "Lombardia",
    "VA": "Lombardia",
    "AN": "Marche",
    "AP": "Marche",
    "FM": "Marche",
    "MC": "Marche",
    "PU": "Marche",
    "CB": "Molise",
    "IS": "Molise",
    "AL": "Piemonte",
    "AT": "Piemonte",
    "BI": "Piemonte",
    "CN": "Piemonte",
    "NO": "Piemonte",
    "TO": "Piemonte",
    "VB": "Piemonte",
    "VC": "Piemonte",
    "BA": "Puglia",
    "BT": "Puglia",
    "BR": "Puglia",
    "FG": "Puglia",
    "LE": "Puglia",
    "TA": "Puglia",
    "CA": "Sardegna",
    "NU": "Sardegna",
    "OR": "Sardegna",
    "SS": "Sardegna",
    "SU": "Sardegna",
    "AG": "Sicilia",
    "CL": "Sicilia",
    "CT": "Sicilia",
    "EN": "Sicilia",
    "ME": "Sicilia",
    "PA": "Sicilia",
    "RG": "Sicilia",
    "SR": "Sicilia",
    "TP": "Sicilia",
    "AR": "Toscana",
    "FI": "Toscana",
    "GR": "Toscana",
    "LI": "Toscana",
    "LU": "Toscana",
    "MS": "Toscana",
    "PI": "Toscana",
    "PT": "Toscana",
    "PO": "Toscana",
    "SI": "Toscana",
    "BZ": "Provincia autonoma di Bolzano",
    "TN": "Provincia autonoma di Trento",
    "PG": "Umbria",
    "TR": "Umbria",
    "AO": "Valle d'Aosta",
    "BL": "Veneto",
    "PD": "Veneto",
    "RO": "Veneto",
    "TV": "Veneto",
    "VE": "Veneto",
    "VR": "Veneto",
    "VI": "Veneto",
}

REGION_CSV_TO_ID = {
    "REGIONE ABRUZZO": "Abruzzo",
    "REGIONE BASILICATA": "Basilicata",
    "REGIONE CALABRIA": "Calabria",
    "REGIONE CAMPANIA": "Campania",
    "REGIONE EMILIA-ROMAGNA": "Emilia-Romagna",
    "REGIONE FRIULI VENEZIA GIULIA": "Friuli-Venezia Giulia",
    "REGIONE LAZIO": "Lazio",
    "REGIONE LIGURIA": "Liguria",
    "REGIONE LOMBARDIA": "Lombardia",
    "REGIONE MARCHE": "Marche",
    "REGIONE MOLISE": "Molise",
    "REGIONE PIEMONTE": "Piemonte",
    "REGIONE PUGLIA": "Puglia",
    "REGIONE SARDEGNA": "Sardegna",
    "REGIONE SICILIA": "Sicilia",
    "REGIONE TOSCANA": "Toscana",
    "REGIONE UMBRIA": "Umbria",
    "REGIONE VALLE D'AOSTA": "Valle d'Aosta",
    "REGIONE VENETO": "Veneto",
    "PROVINCIA AUTONOMA DI BOLZANO": "Provincia autonoma di Bolzano",
    "PROVINCIA AUTONOMA DI TRENTO": "Provincia autonoma di Trento",
}

REGION_ORDER = [
    "Valle d'Aosta",
    "Piemonte",
    "Liguria",
    "Lombardia",
    "Provincia autonoma di Bolzano",
    "Provincia autonoma di Trento",
    "Veneto",
    "Friuli-Venezia Giulia",
    "Emilia-Romagna",
    "Toscana",
    "Umbria",
    "Marche",
    "Lazio",
    "Abruzzo",
    "Molise",
    "Campania",
    "Puglia",
    "Basilicata",
    "Calabria",
    "Sicilia",
    "Sardegna",
]

SMALL = {
    "a",
    "al",
    "alla",
    "alle",
    "con",
    "da",
    "dal",
    "dalla",
    "de",
    "dei",
    "del",
    "dell",
    "della",
    "delle",
    "dello",
    "di",
    "e",
    "ed",
    "in",
    "la",
    "le",
    "nel",
    "nella",
    "su",
    "sul",
}


def title_comune(name: str) -> str:
    parts = re.split(r"([ \-'’])", name.lower())
    out: list[str] = []
    first = True
    for part in parts:
        if part in {" ", "-", "'", "’"}:
            out.append(part)
            continue
        if not part:
            continue
        if not first and part in SMALL:
            out.append(part)
        else:
            out.append(part[:1].upper() + part[1:])
        first = False
    return "".join(out)


def parse_it_number(text: str) -> float | None:
    text = text.strip().replace(" ", "")
    if not text:
        return None
    if "," in text:
        normalized = text.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", text):
        normalized = text.replace(".", "")
    elif re.fullmatch(r"\d+\.\d+", text) or re.fullmatch(r"\d+", text):
        normalized = text
    else:
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def parse_rate(text: str) -> float | None:
    raw = text.strip()
    if not raw or raw == "0*":
        return None
    return parse_it_number(raw)


def parse_fascia_upper(text: str) -> float | None | str:
    fascia = " ".join(text.lower().split())
    if "esenzione" in fascia:
        return "exempt"
    if "aliquota unica" in fascia:
        return None
    numbers = re.findall(
        r"\d{1,3}(?:\.\d{3})+,\d{2}|\d+,\d+|\d+\.\d+|\d+",
        text.replace("euro", " "),
    )
    if "oltre" in fascia and "fino a" not in fascia:
        return None
    if "fino a" in fascia and numbers:
        return parse_it_number(numbers[-1])
    if numbers:
        return parse_it_number(numbers[-1])
    return None


def exemption_from_text(text: str) -> float:
    match = re.search(
        r"fino a(?: euro)?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:[.,]\d+)?)",
        text,
        flags=re.I,
    )
    if not match:
        return 0
    value = parse_it_number(match.group(1))
    return value or 0


def municipal_from_row(row: dict[str, str]) -> dict:
    star = row["ALIQUOTA"].strip() == "0*"
    exemption = parse_it_number(row.get("IMPORTO_ESENTE") or "0") or 0
    brackets: list[list] = []
    if star:
        return {"e": 0, "b": [[None, 0]], "star": True}

    for i in range(1, 13):
        suffix = "" if i == 1 else f"_{i}"
        rate_raw = (row.get(f"ALIQUOTA{suffix}") or "").strip()
        fascia = (row.get(f"FASCIA{suffix}") or "").strip()
        if not rate_raw and not fascia:
            continue
        kind = parse_fascia_upper(fascia) if fascia else None
        if kind == "exempt":
            if not exemption:
                exemption = exemption_from_text(fascia)
            continue
        rate = parse_rate(rate_raw)
        if rate is None:
            continue
        upper = None if kind is None else kind
        brackets.append([upper, rate])

    if not brackets:
        brackets = [[None, 0]]
    payload = {"e": exemption, "b": brackets}
    return payload


def _xlsx_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in root.findall("m:si", XLSX_NS):
        strings.append("".join(node.text or "" for node in si.findall(".//m:t", XLSX_NS)))
    return strings


def _xlsx_cell_text(cell: ET.Element, strings: list[str]) -> str:
    kind = cell.get("t")
    value = cell.find("m:v", XLSX_NS)
    if kind == "s" and value is not None and value.text is not None:
        return strings[int(value.text)]
    if kind == "inlineStr":
        inline = cell.find("m:is", XLSX_NS)
        if inline is not None:
            return "".join(node.text or "" for node in inline.findall(".//m:t", XLSX_NS))
    if value is not None and value.text is not None:
        return value.text
    return ""


def _xlsx_row_values(row: ET.Element, strings: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for cell in row.findall("m:c", XLSX_NS):
        ref = cell.get("r") or ""
        col = "".join(ch for ch in ref if ch.isalpha())
        values[col] = _xlsx_cell_text(cell, strings).strip()
    return values


def municipal_from_xlsx_row(values: dict[str, str]) -> dict:
    unique = parse_rate(values.get("D") or "")
    progressive = [
        rate
        for raw in (values.get("E"), values.get("F"), values.get("G"), values.get("H"))
        if (rate := parse_rate(raw or "")) is not None
    ]
    exemption = parse_it_number(values.get("I") or "") or 0
    if unique is not None and not progressive:
        return {"e": exemption, "b": [[None, unique]]}
    uppers = PROGRESSIVE_UPPERS.get(len(progressive))
    if unique is None and uppers is not None:
        return {"e": exemption, "b": [[upper, rate] for upper, rate in zip(uppers, progressive)]}
    if not progressive and unique is None:
        return {"e": exemption, "b": [[None, 0]]}
    raise ValueError(
        f"Unexpected municipal rates for {values.get('A')}: unique={unique!r} progressive={progressive!r}"
    )


def load_municipal_xlsx() -> tuple[dict[str, list[dict]], list[tuple[str, str, str]]]:
    cities: dict[str, list[dict]] = defaultdict(list)
    skipped: list[tuple[str, str, str]] = []
    with zipfile.ZipFile(MUNICIPAL) as archive:
        strings = _xlsx_shared_strings(archive)
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        for row in sheet.findall("m:sheetData/m:row", XLSX_NS):
            values = _xlsx_row_values(row, strings)
            code = (values.get("A") or "").strip()
            name = (values.get("B") or "").strip()
            province = (values.get("C") or "").strip()
            if not code or code.lower().startswith("codice") or not name:
                continue
            region = PROVINCE_TO_REGION.get(province)
            if not region:
                skipped.append((code, name, province))
                continue
            parsed = municipal_from_xlsx_row(values)
            cities[region].append(
                {
                    "id": code,
                    "n": title_comune(name),
                    "p": province,
                    **parsed,
                }
            )
    for region in cities:
        cities[region].sort(key=lambda item: (item["n"], item["id"]))
    return cities, skipped


def load_regional() -> dict[str, dict]:
    grouped: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    with REGIONAL.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle, delimiter=";"):
            name = REGION_CSV_TO_ID.get(row["REGIONE"].strip())
            if not name:
                continue
            number = row["NUMERO"].strip()
            fascia = (row.get("FASCIA ") or row.get("FASCIA") or "").strip()
            rate = parse_it_number(row["ALIQUOTA"].strip())
            if rate is None:
                continue
            upper = parse_fascia_upper(fascia)
            if upper == "exempt":
                continue
            grouped[name][number].append(
                {
                    "upper": None if upper is None else upper,
                    "rate": rate,
                    "disp": row.get("DISPOSIZIONE") or "",
                    "fascia": fascia,
                }
            )

    regions: dict[str, dict] = {}
    for name, by_number in grouped.items():
        latest = max(by_number, key=lambda key: int(key) if key.isdigit() else 0)
        rows = by_number[latest]
        exemption = 0.0
        disp = rows[0]["disp"]
        if re.search(r"esentat", disp, flags=re.I):
            exemption = exemption_from_text(disp)
        brackets = [[row["upper"], row["rate"]] for row in rows]
        regions[name] = {"e": exemption, "b": brackets}
    return regions


def main() -> None:
    cities, skipped = load_municipal_xlsx()
    regions = load_regional()
    payload = {
        "year": 2025,
        "regions": [
            {"id": name, "n": name, **regions[name]}
            for name in REGION_ORDER
            if name in regions
        ],
        "cities": {name: cities.get(name, []) for name in REGION_ORDER},
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size = OUT.stat().st_size
    n_cities = sum(len(v) for v in payload["cities"].values())
    print(f"Wrote {OUT} ({size} bytes, {n_cities} cities, {len(payload['regions'])} regions)")
    if skipped:
        by_pr: dict[str, int] = defaultdict(int)
        for _code, _name, province in skipped:
            by_pr[province or "(empty)"] += 1
        print(f"Skipped {len(skipped)} cities with unknown province codes: {dict(by_pr)}")
        for code, name, province in skipped[:20]:
            print(f"  {code} {name} PR={province!r}")


if __name__ == "__main__":
    main()
