(function (root) {
  "use strict";

  const MONTHS = 13;
  const SCALE = 100000000n;
  const CENT = 1000000n;

  const INPS_EMPLOYEE_NUM = 919n;
  const INPS_EMPLOYEE_DEN = 10000n;
  const INPS_EXTRA_NUM = 1n;
  const INPS_EXTRA_DEN = 100n;
  const INPS_MASSIMALE = fromEuro(122295);
  const INPS_PRIMA_FASCIA = fromEuro(56224);

  const IRPEF_BRACKETS = [
    [fromEuro(28000), 23n, 100n],
    [fromEuro(50000), 33n, 100n],
    [null, 43n, 100n],
  ];

  const DET_LOW_INCOME = fromEuro(1955);
  const DET_MID_BASE = fromEuro(1910);
  const DET_MID_EXTRA = fromEuro(1190);
  const DET_MID_SPAN = fromEuro(13000);
  const DET_HIGH_SPAN = fromEuro(22000);
  const DET_BAND_15K = fromEuro(15000);
  const DET_BAND_28K = fromEuro(28000);
  const DET_BAND_50K = fromEuro(50000);
  const DET_EXTRA_65 = fromEuro(65);
  const DET_EXTRA_65_FROM = fromEuro(25000);
  const DET_EXTRA_65_TO = fromEuro(35000);
  const DET_FLOOR_PERMANENT = fromEuro(690);

  const TI_AMOUNT = fromEuro(1200);
  const TI_FULL_LIMIT = fromEuro(15000);
  const TI_REDUCED_LIMIT = fromEuro(28000);
  const TI_CAPIENZA_REDUCTION = fromEuro(75);

  const CUNEO_CASH_LIMIT = fromEuro(20000);
  const CUNEO_CREDIT_FLAT_TO = fromEuro(32000);
  const CUNEO_CREDIT_END = fromEuro(40000);
  const CUNEO_CREDIT_FLAT = fromEuro(1000);
  const CUNEO_CREDIT_SPAN = fromEuro(8000);
  const CUNEO_EMP_BAND_8500 = fromEuro(8500);
  const CUNEO_EMP_BAND_15000 = fromEuro(15000);

  const LOMBARDY_BRACKETS = [
    [fromEuro(15000), 123n, 10000n],
    [fromEuro(28000), 158n, 10000n],
    [fromEuro(50000), 172n, 10000n],
    [null, 173n, 10000n],
  ];

  const MILAN_NUM = 8n;
  const MILAN_DEN = 1000n;
  const MILAN_EXEMPTION = fromEuro(23000);
  const IRPEF_MIN_DUE = fromEuro(12);

  function fromEuro(value) {
    const sign = value < 0 ? -1n : 1n;
    const text = Math.abs(Number(value)).toFixed(8);
    const [whole, frac = ""] = text.split(".");
    const frac8 = (frac + "00000000").slice(0, 8);
    return sign * (BigInt(whole) * SCALE + BigInt(frac8));
  }

  function toNumber(scaled) {
    const sign = scaled < 0n ? -1 : 1;
    const abs = scaled < 0n ? -scaled : scaled;
    const whole = abs / SCALE;
    const frac = abs % SCALE;
    return sign * Number(whole) + sign * Number(frac) / Number(SCALE);
  }

  function euro(scaled) {
    const sign = scaled < 0n ? -1n : 1n;
    const abs = scaled < 0n ? -scaled : scaled;
    return sign * ((abs + CENT / 2n) / CENT) * CENT;
  }

  function mulRate(amount, num, den) {
    return (amount * num) / den;
  }

  function ratio4dp(numerator, denominator) {
    if (denominator <= 0n || numerator <= 0n) return 0n;
    const four = 10000n;
    const q = (numerator * four * SCALE) / denominator;
    return (q / SCALE) * (SCALE / four);
  }

  function taxOnBrackets(income, brackets) {
    if (income <= 0n) return 0n;
    let tax = 0n;
    let lower = 0n;
    for (const [upper, num, den] of brackets) {
      const sliceEnd = upper == null || income < upper ? income : upper;
      if (sliceEnd > lower) {
        tax += mulRate(sliceEnd - lower, num, den);
      }
      if (upper == null || income <= upper) break;
      lower = upper;
    }
    return tax;
  }

  function employeeInps(ral) {
    const base = ral < INPS_MASSIMALE ? ral : INPS_MASSIMALE;
    let contribution = mulRate(base, INPS_EMPLOYEE_NUM, INPS_EMPLOYEE_DEN);
    const extraBase = base - INPS_PRIMA_FASCIA;
    if (extraBase > 0n) {
      contribution += mulRate(extraBase, INPS_EXTRA_NUM, INPS_EXTRA_DEN);
    }
    return euro(contribution);
  }

  function irpefGross(imponibile) {
    return euro(taxOnBrackets(imponibile, IRPEF_BRACKETS));
  }

  function employeeTaxCredit(rc) {
    let base;
    if (rc <= DET_BAND_15K) {
      base = DET_LOW_INCOME > DET_FLOOR_PERMANENT ? DET_LOW_INCOME : DET_FLOOR_PERMANENT;
    } else if (rc <= DET_BAND_28K) {
      base = DET_MID_BASE + mulRate(DET_MID_EXTRA, ratio4dp(DET_BAND_28K - rc, DET_MID_SPAN), SCALE);
    } else if (rc <= DET_BAND_50K) {
      base = mulRate(DET_MID_BASE, ratio4dp(DET_BAND_50K - rc, DET_HIGH_SPAN), SCALE);
    } else {
      base = 0n;
    }
    const extra65 =
      rc > DET_EXTRA_65_FROM && rc <= DET_EXTRA_65_TO ? DET_EXTRA_65 : 0n;
    return [euro(base), extra65];
  }

  function cuneoRelief(rc) {
    if (rc <= CUNEO_CASH_LIMIT) {
      let num = 48n;
      let den = 1000n;
      if (rc <= CUNEO_EMP_BAND_8500) {
        num = 71n;
        den = 1000n;
      } else if (rc <= CUNEO_EMP_BAND_15000) {
        num = 53n;
        den = 1000n;
      }
      return [euro(mulRate(rc, num, den)), 0n];
    }
    if (rc <= CUNEO_CREDIT_FLAT_TO) return [0n, CUNEO_CREDIT_FLAT];
    if (rc <= CUNEO_CREDIT_END) {
      return [
        0n,
        euro(mulRate(CUNEO_CREDIT_FLAT, CUNEO_CREDIT_END - rc, CUNEO_CREDIT_SPAN)),
      ];
    }
    return [0n, 0n];
  }

  function trattamentoIntegrativo(rc, irpefLorda, detrazioneLavoro) {
    if (rc <= TI_FULL_LIMIT) {
      if (irpefLorda > detrazioneLavoro - TI_CAPIENZA_REDUCTION) return TI_AMOUNT;
      return 0n;
    }
    if (rc <= TI_REDUCED_LIMIT) {
      const gap = detrazioneLavoro - irpefLorda;
      if (gap > 0n) {
        const rounded = euro(gap);
        return rounded < TI_AMOUNT ? rounded : TI_AMOUNT;
      }
      return 0n;
    }
    return 0n;
  }

  function lombardySurcharge(imponibile) {
    return euro(taxOnBrackets(imponibile, LOMBARDY_BRACKETS));
  }

  function milanSurcharge(imponibile) {
    if (imponibile <= MILAN_EXEMPTION) return 0n;
    return euro(mulRate(imponibile, MILAN_NUM, MILAN_DEN));
  }

  function money(scaled) {
    return toNumber(euro(scaled));
  }

  function calculateNet(ralNumber) {
    if (ralNumber <= 0) throw new Error("La RAL deve essere positiva");
    const ral = euro(fromEuro(ralNumber));
    const inps = employeeInps(ral);
    const imponibile = euro(ral - inps);
    const irpefLorda = irpefGross(imponibile);
    const [detBase, det65] = employeeTaxCredit(imponibile);
    const detLavoro = euro(detBase + det65);
    const [cuneoBonus, cuneoCredit] = cuneoRelief(imponibile);

    let irpefNetta = irpefLorda - detLavoro - cuneoCredit;
    if (irpefNetta < 0n) irpefNetta = 0n;

    let regionale = 0n;
    let comunale = 0n;
    if (irpefNetta > IRPEF_MIN_DUE) {
      regionale = lombardySurcharge(imponibile);
      comunale = milanSurcharge(imponibile);
    }
    const ti = trattamentoIntegrativo(imponibile, irpefLorda, detLavoro);
    const netAnnual = euro(
      ral - inps - irpefNetta - regionale - comunale + ti + cuneoBonus
    );

    return {
      ral: money(ral),
      inps: money(inps),
      imponibile: money(imponibile),
      irpefLorda: money(irpefLorda),
      detrazioneLavoro: money(detBase),
      detrazione65: money(det65),
      cuneoCredit: money(cuneoCredit),
      irpefNetta: money(irpefNetta),
      addizionaleRegionale: money(regionale),
      addizionaleComunale: money(comunale),
      trattamentoIntegrativo: money(ti),
      cuneoBonus: money(cuneoBonus),
      netAnnual: money(netAnnual),
      netMonthly: money(euro((netAnnual * SCALE) / fromEuro(MONTHS))),
    };
  }

  function fmtIt(value) {
    const sign = value < 0 ? "-" : "";
    const absCents = Math.round(Math.abs(value) * 100);
    const whole = Math.floor(absCents / 100);
    const frac = String(absCents % 100).padStart(2, "0");
    const wholeFmt = String(whole).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return sign + wholeFmt + "," + frac;
  }

  function fmt(amount) {
    const sign = amount < 0 ? "-" : "";
    return sign + "€" + fmtIt(Math.abs(amount));
  }

  function pctOf(amount, base) {
    return money(euro((fromEuro(amount) * fromEuro(100)) / fromEuro(base)));
  }

  function fmtPct(amount, base) {
    return fmtIt(pctOf(amount, base)) + "%";
  }

  function breakdownRows(result) {
    return [
      { label: "RAL (lordo annuo)", calc: null, withheld: result.ral, sectionBreak: false, indent: false },
      { label: "Contributi INPS dipendente", calc: null, withheld: -result.inps, sectionBreak: false, indent: false },
      { label: "Imponibile fiscale", calc: result.imponibile, withheld: null, sectionBreak: true, indent: false },
      { label: "IRPEF lorda", calc: result.irpefLorda, withheld: null, sectionBreak: false, indent: false },
      { label: "Detrazione lavoro dipendente", calc: -result.detrazioneLavoro, withheld: null, sectionBreak: false, indent: true },
      { label: "Maggiorazione 65 euro", calc: -result.detrazione65, withheld: null, sectionBreak: false, indent: true },
      { label: "Detrazione cuneo fiscale", calc: -result.cuneoCredit, withheld: null, sectionBreak: false, indent: true },
      { label: "IRPEF netta", calc: result.irpefNetta, withheld: -result.irpefNetta, sectionBreak: false, indent: false },
      { label: "Addizionale regionale Lombardia", calc: null, withheld: -result.addizionaleRegionale, sectionBreak: false, indent: false },
      { label: "Addizionale comunale Milano", calc: null, withheld: -result.addizionaleComunale, sectionBreak: false, indent: false },
      { label: "Trattamento integrativo", calc: null, withheld: result.trattamentoIntegrativo, sectionBreak: false, indent: false },
      { label: "Somma esente cuneo fiscale", calc: null, withheld: result.cuneoBonus, sectionBreak: true, indent: false },
      { label: "Netto annuo", calc: null, withheld: result.netAnnual, sectionBreak: false, indent: false },
      { label: "Netto mensile (annuo / " + MONTHS + ")", calc: null, withheld: result.netMonthly, sectionBreak: false, indent: false },
    ];
  }

  function trattenutePct(amount, ral) {
    if (amount == null || amount === 0) return null;
    return pctOf(amount, ral);
  }

  function displayRows(result) {
    const monthlyLabel = "Netto mensile (annuo / " + MONTHS + ")";
    const contributing = [];
    const staged = breakdownRows(result).map((row) => {
      let pctVal = null;
      if (row.label !== "Netto annuo" && row.label !== monthlyLabel) {
        pctVal = trattenutePct(row.withheld, result.ral);
        if (pctVal != null) contributing.push(pctVal);
      }
      return [row, pctVal];
    });
    const netPct = contributing.reduce((a, b) => a + b, 0);
    return staged.map(([row, pctVal]) => {
      let pct = "";
      if (row.label === "Netto annuo") pct = fmtIt(netPct) + "%";
      else if (pctVal != null) pct = fmtIt(pctVal) + "%";
      return {
        label: row.label,
        calc: row.calc != null ? fmt(row.calc) : "",
        withheld: row.withheld != null ? fmt(row.withheld) : "",
        pct,
        sectionBreak: row.sectionBreak,
        indent: row.indent,
        emphasis: row.label.startsWith("Netto"),
      };
    });
  }

  function prettyStep(raw) {
    const value = Number(raw);
    if (value <= 0) return 100;
    const magnitude = 10 ** Math.floor(Math.log10(value));
    for (const multiplier of [1, 2, 2.5, 5, 10]) {
      const step = magnitude * multiplier;
      if (step >= value * 0.85) return money(euro(fromEuro(step)));
    }
    return money(euro(fromEuro(magnitude * 10)));
  }

  function comparisonCurve(center, sides) {
    if (sides == null) sides = 5;
    let step = prettyStep(center * 0.08);
    const floor = 100;
    while (sides * step >= center - floor && step > 1) {
      const halved = money(euro(fromEuro(step / 2)));
      if (halved < 1) {
        step = 1;
        break;
      }
      step = halved;
    }

    const points = [];
    for (let offset = -sides; offset <= sides; offset += 1) {
      const ral = money(euro(fromEuro(center + offset * step)));
      if (ral <= 0) continue;
      const result = calculateNet(ral);
      points.push({
        ral: result.ral,
        net: result.netAnnual,
        pct: pctOf(result.netAnnual, result.ral),
        ral_label: fmt(result.ral),
        net_label: fmt(result.netAnnual),
        pct_label: fmtPct(result.netAnnual, result.ral),
        selected: offset === 0,
      });
    }
    return points;
  }

  function parseRal(text) {
    let cleaned = String(text).trim().replace(/_/g, "").replace(/ /g, "");
    if (cleaned.includes(",") && cleaned.includes(".")) {
      cleaned = cleaned.replace(/\./g, "").replace(",", ".");
    } else if (cleaned.includes(",")) {
      cleaned = cleaned.replace(",", ".");
    }
    const value = Number(cleaned);
    if (!Number.isFinite(value)) {
      throw new Error("La RAL deve essere un numero, ad es. 35000");
    }
    if (value <= 0) throw new Error("La RAL deve essere positiva");
    return value;
  }

  const api = {
    MONTHS,
    calculateNet,
    displayRows,
    comparisonCurve,
    parseRal,
    fmt,
    fmtIt,
    fmtPct,
  };

  root.NetIncome = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
