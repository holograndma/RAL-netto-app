#!/usr/bin/env python3
"""Stima dello stipendio netto 2026 per un dipendente del settore privato a Milano.

Ipotesi:
- Tempo pieno, contratto a tempo indeterminato, residente a Milano
- RAL erogata su 13 mensilità
- Solo reddito da lavoro dipendente; nessun familiare a carico né altre detrazioni
- Iscritto dopo il 1995 (si applica il massimale INPS)
- Conguaglio annuale, non una simulazione mese per mese del cedolino

Stima indicativa, non consulenza fiscale.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
FOUR_DP = Decimal("0.0001")
MONTHS = 13

# INPS 2026 (Circolare INPS n. 6/2026 and n. 27/2026)
INPS_EMPLOYEE_RATE = Decimal("0.0919")
INPS_EXTRA_RATE = Decimal("0.01")
INPS_MASSIMALE = Decimal("122295")
INPS_PRIMA_FASCIA = Decimal("56224")

# IRPEF 2026 — art. 11 TUIR as amended by L. 199/2025 art. 1 c. 3
IRPEF_BRACKETS = (
    (Decimal("28000"), Decimal("0.23")),
    (Decimal("50000"), Decimal("0.33")),
    (None, Decimal("0.43")),
)

# Art. 13 TUIR employee credit
DET_LOW_INCOME = Decimal("1955")
DET_MID_BASE = Decimal("1910")
DET_MID_EXTRA = Decimal("1190")
DET_MID_SPAN = Decimal("13000")
DET_HIGH_SPAN = Decimal("22000")
DET_BAND_15K = Decimal("15000")
DET_BAND_28K = Decimal("28000")
DET_BAND_50K = Decimal("50000")
DET_EXTRA_65 = Decimal("65")
DET_EXTRA_65_FROM = Decimal("25000")
DET_EXTRA_65_TO = Decimal("35000")
DET_FLOOR_PERMANENT = Decimal("690")

# Trattamento integrativo — D.L. 3/2020
TI_AMOUNT = Decimal("1200")
TI_FULL_LIMIT = Decimal("15000")
TI_REDUCED_LIMIT = Decimal("28000")
TI_CAPIENZA_REDUCTION = Decimal("75")

# Cuneo fiscale — L. 207/2024 art. 1 c. 4-6
CUNEO_CASH_LIMIT = Decimal("20000")
CUNEO_CREDIT_FLAT_TO = Decimal("32000")
CUNEO_CREDIT_END = Decimal("40000")
CUNEO_CREDIT_FLAT = Decimal("1000")
CUNEO_CREDIT_SPAN = Decimal("8000")
CUNEO_EMP_BAND_8500 = Decimal("8500")
CUNEO_EMP_BAND_15000 = Decimal("15000")
CUNEO_PCT_LOW = Decimal("0.071")
CUNEO_PCT_MID = Decimal("0.053")
CUNEO_PCT_HIGH = Decimal("0.048")

# Lombardy regional surcharge 2026 (MEF)
LOMBARDY_BRACKETS = (
    (Decimal("15000"), Decimal("0.0123")),
    (Decimal("28000"), Decimal("0.0158")),
    (Decimal("50000"), Decimal("0.0172")),
    (None, Decimal("0.0173")),
)

# Milan municipal surcharge (Comune di Milano: 0.80%, exemption ≤ €23,000)
MILAN_RATE = Decimal("0.008")
MILAN_EXEMPTION = Decimal("23000")

# Art. 50 D.Lgs. 446/1997; Circolare 3/E/1998: addizionali not due if net IRPEF ≤ €12
IRPEF_MIN_DUE = Decimal("12")


def euro(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def ratio_4dp(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Art. 13 c. 6 TUIR: keep the first four decimal places of the ratio."""
    if denominator <= 0 or numerator <= 0:
        return ZERO
    return (numerator / denominator).quantize(FOUR_DP, rounding=ROUND_DOWN)


def tax_on_brackets(
    income: Decimal,
    brackets: tuple[tuple[Decimal | None, Decimal], ...],
) -> Decimal:
    if income <= 0:
        return ZERO
    tax = ZERO
    lower = ZERO
    for upper, rate in brackets:
        slice_end = income if upper is None else min(income, upper)
        if slice_end > lower:
            tax += (slice_end - lower) * rate
        if upper is None or income <= upper:
            break
        lower = upper
    return tax


def employee_inps(ral: Decimal) -> Decimal:
    base = min(ral, INPS_MASSIMALE)
    contribution = base * INPS_EMPLOYEE_RATE
    extra_base = min(base, INPS_MASSIMALE) - INPS_PRIMA_FASCIA
    if extra_base > 0:
        contribution += extra_base * INPS_EXTRA_RATE
    return euro(contribution)


def irpef_gross(imponibile: Decimal) -> Decimal:
    return euro(tax_on_brackets(imponibile, IRPEF_BRACKETS))


def employee_tax_credit(reddito_complessivo: Decimal) -> tuple[Decimal, Decimal]:
    rc = reddito_complessivo
    if rc <= DET_BAND_15K:
        base = max(DET_LOW_INCOME, DET_FLOOR_PERMANENT)
    elif rc <= DET_BAND_28K:
        base = DET_MID_BASE + DET_MID_EXTRA * ratio_4dp(
            DET_BAND_28K - rc, DET_MID_SPAN
        )
    elif rc <= DET_BAND_50K:
        base = DET_MID_BASE * ratio_4dp(DET_BAND_50K - rc, DET_HIGH_SPAN)
    else:
        base = ZERO

    extra_65 = (
        DET_EXTRA_65 if DET_EXTRA_65_FROM < rc <= DET_EXTRA_65_TO else ZERO
    )
    return euro(base), extra_65


def cuneo_relief(reddito_complessivo: Decimal) -> tuple[Decimal, Decimal]:
    """Return (tax-free cash bonus, extra IRPEF credit). Mutually exclusive bands."""
    rc = reddito_complessivo
    if rc <= CUNEO_CASH_LIMIT:
        if rc <= CUNEO_EMP_BAND_8500:
            rate = CUNEO_PCT_LOW
        elif rc <= CUNEO_EMP_BAND_15000:
            rate = CUNEO_PCT_MID
        else:
            rate = CUNEO_PCT_HIGH
        return euro(rc * rate), ZERO
    if rc <= CUNEO_CREDIT_FLAT_TO:
        return ZERO, CUNEO_CREDIT_FLAT
    if rc <= CUNEO_CREDIT_END:
        return ZERO, euro(
            CUNEO_CREDIT_FLAT * (CUNEO_CREDIT_END - rc) / CUNEO_CREDIT_SPAN
        )
    return ZERO, ZERO


def trattamento_integrativo(
    reddito_complessivo: Decimal,
    irpef_lorda: Decimal,
    detrazione_lavoro: Decimal,
) -> Decimal:
    rc = reddito_complessivo
    if rc <= TI_FULL_LIMIT:
        if irpef_lorda > detrazione_lavoro - TI_CAPIENZA_REDUCTION:
            return TI_AMOUNT
        return ZERO
    if rc <= TI_REDUCED_LIMIT:
        gap = detrazione_lavoro - irpef_lorda
        if gap > 0:
            return min(TI_AMOUNT, euro(gap))
        return ZERO
    return ZERO


def lombardy_surcharge(imponibile: Decimal) -> Decimal:
    return euro(tax_on_brackets(imponibile, LOMBARDY_BRACKETS))


def milan_surcharge(imponibile: Decimal) -> Decimal:
    if imponibile <= MILAN_EXEMPTION:
        return ZERO
    return euro(imponibile * MILAN_RATE)


@dataclass(frozen=True)
class BreakdownRow:
    label: str
    calc: Decimal | None
    withheld: Decimal | None
    show_pct: bool
    section_break: bool = False
    indent: bool = False


@dataclass(frozen=True)
class NetIncome:
    ral: Decimal
    inps: Decimal
    imponibile: Decimal
    irpef_lorda: Decimal
    detrazione_lavoro: Decimal
    detrazione_65: Decimal
    cuneo_credit: Decimal
    irpef_netta: Decimal
    addizionale_regionale: Decimal
    addizionale_comunale: Decimal
    trattamento_integrativo: Decimal
    cuneo_bonus: Decimal
    net_annual: Decimal
    net_monthly: Decimal


def calculate_net(ral: Decimal) -> NetIncome:
    if ral <= 0:
        raise ValueError("La RAL deve essere positiva")

    inps = employee_inps(ral)
    imponibile = euro(ral - inps)
    irpef_lorda = irpef_gross(imponibile)

    det_base, det_65 = employee_tax_credit(imponibile)
    det_lavoro = euro(det_base + det_65)
    cuneo_bonus, cuneo_credit = cuneo_relief(imponibile)

    irpef_netta = irpef_lorda - det_lavoro - cuneo_credit
    if irpef_netta < 0:
        irpef_netta = ZERO

    if irpef_netta > IRPEF_MIN_DUE:
        regionale = lombardy_surcharge(imponibile)
        comunale = milan_surcharge(imponibile)
    else:
        regionale = ZERO
        comunale = ZERO
    ti = trattamento_integrativo(imponibile, irpef_lorda, det_lavoro)

    net_annual = euro(
        ral - inps - irpef_netta - regionale - comunale + ti + cuneo_bonus
    )
    return NetIncome(
        ral=euro(ral),
        inps=inps,
        imponibile=imponibile,
        irpef_lorda=irpef_lorda,
        detrazione_lavoro=det_base,
        detrazione_65=det_65,
        cuneo_credit=cuneo_credit,
        irpef_netta=irpef_netta,
        addizionale_regionale=regionale,
        addizionale_comunale=comunale,
        trattamento_integrativo=ti,
        cuneo_bonus=cuneo_bonus,
        net_annual=net_annual,
        net_monthly=euro(net_annual / MONTHS),
    )


def fmt_it(value: Decimal) -> str:
    sign = "-" if value < 0 else ""
    body = f"{abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}{body}"


def fmt(amount: Decimal) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}€{fmt_it(abs(amount))}"


def fmt_pct(amount: Decimal, base: Decimal) -> str:
    pct = (amount / base * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
    return f"{fmt_it(pct)}%"


def breakdown_rows(result: NetIncome) -> list[BreakdownRow]:
    return [
        BreakdownRow("RAL (lordo annuo)", None, result.ral, False),
        BreakdownRow("Contributi INPS dipendente", None, -result.inps, True),
        BreakdownRow(
            "Imponibile fiscale", result.imponibile, None, False, section_break=True
        ),
        BreakdownRow("IRPEF lorda", result.irpef_lorda, None, False),
        BreakdownRow(
            "Detrazione lavoro dipendente",
            -result.detrazione_lavoro,
            None,
            False,
            indent=True,
        ),
        BreakdownRow(
            "Maggiorazione 65 euro", -result.detrazione_65, None, False, indent=True
        ),
        BreakdownRow(
            "Detrazione cuneo fiscale",
            -result.cuneo_credit,
            None,
            False,
            indent=True,
        ),
        BreakdownRow("IRPEF netta", result.irpef_netta, -result.irpef_netta, True),
        BreakdownRow(
            "Addizionale regionale Lombardia",
            None,
            -result.addizionale_regionale,
            True,
        ),
        BreakdownRow(
            "Addizionale comunale Milano",
            None,
            -result.addizionale_comunale,
            True,
        ),
        BreakdownRow(
            "Trattamento integrativo", None, result.trattamento_integrativo, False
        ),
        BreakdownRow(
            "Somma esente cuneo fiscale",
            None,
            result.cuneo_bonus,
            False,
            section_break=True,
        ),
        BreakdownRow("Netto annuo", None, result.net_annual, True),
        BreakdownRow(
            f"Netto mensile (annuo / {MONTHS})", None, result.net_monthly, False
        ),
    ]


AMOUNT_W = 14
PCT_W = 11


def trattenute_pct(amount: Decimal | None, ral: Decimal) -> Decimal | None:
    if amount is None or amount == 0:
        return None
    return (amount / ral * Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)


def display_rows(result: NetIncome) -> list[dict[str, str | bool]]:
    monthly_label = f"Netto mensile (annuo / {MONTHS})"
    contributing: list[Decimal] = []
    staged: list[tuple[BreakdownRow, Decimal | None]] = []
    for row in breakdown_rows(result):
        if row.label in {"Netto annuo", monthly_label}:
            pct_val = None
        else:
            pct_val = trattenute_pct(row.withheld, result.ral)
            if pct_val is not None:
                contributing.append(pct_val)
        staged.append((row, pct_val))

    net_pct = sum(contributing, ZERO)
    rows: list[dict[str, str | bool]] = []
    for row, pct_val in staged:
        if row.label == "Netto annuo":
            pct = f"{fmt_it(net_pct)}%"
        elif pct_val is None:
            pct = ""
        else:
            pct = f"{fmt_it(pct_val)}%"
        rows.append(
            {
                "label": row.label,
                "calc": fmt(row.calc) if row.calc is not None else "",
                "withheld": fmt(row.withheld) if row.withheld is not None else "",
                "pct": pct,
                "section_break": row.section_break,
                "indent": row.indent,
                "emphasis": row.label.startswith("Netto"),
            }
        )
    return rows


def render(result: NetIncome) -> str:
    rows = display_rows(result)
    width = max(len(row["label"]) + (2 if row["indent"] else 0) for row in rows)
    header = (
        f"{'':<{width}}  {'Calcolo':>{AMOUNT_W}}  "
        f"{'Trattenute':>{AMOUNT_W}}  {'% sul lordo':>{PCT_W}}"
    )
    lines = [
        "Stipendio netto 2026 — Dipendente settore privato, Milano",
        "Ipotesi: 13 mensilità, nessun familiare a carico, nessuna altra detrazione",
        "",
        header,
    ]
    for row in rows:
        label = ("  " + row["label"]) if row["indent"] else row["label"]
        calc = f"{row['calc']:>{AMOUNT_W}}" if row["calc"] else " " * AMOUNT_W
        withheld = (
            f"{row['withheld']:>{AMOUNT_W}}" if row["withheld"] else " " * AMOUNT_W
        )
        pct = f"{row['pct']:>{PCT_W}}" if row["pct"] else " " * PCT_W
        lines.append(f"{label:<{width}}  {calc}  {withheld}  {pct}")
        if row["section_break"]:
            lines.append("")
    lines.extend(
        [
            "",
            "Le percentuali delle trattenute e degli accrediti sono sulla RAL; "
            "il netto annuo è la loro somma.",
            "Stima indicativa. Non è un cedolino e non costituisce consulenza fiscale.",
        ]
    )
    return "\n".join(lines)


def _pretty_step(raw: Decimal) -> Decimal:
    value = float(raw)
    if value <= 0:
        return Decimal("100")
    magnitude = 10 ** math.floor(math.log10(value))
    for multiplier in (1, 2, 2.5, 5, 10):
        step = magnitude * multiplier
        if step >= value * 0.85:
            return euro(Decimal(str(step)))
    return euro(Decimal(str(magnitude * 10)))


def comparison_curve(center: Decimal, sides: int = 5) -> list[dict[str, float | str | bool]]:
    """Net pay points with the chosen RAL in the middle of the series."""
    step = _pretty_step(center * Decimal("0.08"))
    floor = Decimal("100")
    while sides * step >= center - floor and step > Decimal("1"):
        halved = euro(step / 2)
        if halved < Decimal("1"):
            step = Decimal("1")
            break
        step = halved

    points: list[dict[str, float | str | bool]] = []
    for offset in range(-sides, sides + 1):
        ral = euro(center + offset * step)
        if ral <= 0:
            continue
        result = calculate_net(ral)
        points.append(
            {
                "ral": float(result.ral),
                "net": float(result.net_annual),
                "pct": float(
                    (result.net_annual / result.ral * Decimal("100")).quantize(CENT)
                ),
                "ral_label": fmt(result.ral),
                "net_label": fmt(result.net_annual),
                "pct_label": fmt_pct(result.net_annual, result.ral),
                "selected": offset == 0,
            }
        )
    return points


def parse_ral(text: str) -> Decimal:
    cleaned = text.strip().replace("_", "").replace(" ", "")
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        value = Decimal(cleaned)
    except Exception as exc:
        raise ValueError("La RAL deve essere un numero, ad es. 35000") from exc
    if value <= 0:
        raise ValueError("La RAL deve essere positiva")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Stima del reddito netto 2026 per un dipendente del settore privato a Milano."
        )
    )

    def ral_arg(text: str) -> Decimal:
        try:
            return parse_ral(text)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(str(exc)) from exc

    parser.add_argument(
        "ral", type=ral_arg, help="Retribuzione annua lorda (RAL) in euro"
    )
    args = parser.parse_args(argv)
    print(render(calculate_net(args.ral)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
