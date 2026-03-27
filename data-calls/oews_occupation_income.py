"""
BLS OEWS — Boston MSA Occupation Wage Data
===========================================
BLS blocks automated downloads. Download the zip files manually in your
browser and place them in the ZIPS_DIR folder below, then run this script.

DOWNLOAD URLS (paste each into browser address bar):
  https://www.bls.gov/oes/special.requests/oesm05ma.zip
  https://www.bls.gov/oes/special.requests/oesm09ma.zip
  https://www.bls.gov/oes/special.requests/oesm12ma.zip
  https://www.bls.gov/oes/special.requests/oesm15ma.zip
  https://www.bls.gov/oes/special.requests/oesm19ma.zip
  https://www.bls.gov/oes/special.requests/oesm21ma.zip
  https://www.bls.gov/oes/special.requests/oesm22ma.zip
  https://www.bls.gov/oes/special.requests/oesm23ma.zip

RUN:
    python fetch_oews_occupations.py

OUTPUT:
    ./outputs/oews_boston_occupations.csv   — one row per occupation per year
    ./outputs/oews_boston_wide.csv          — one row per occupation, years as columns
    ./outputs/oews_boston_monthly.csv       — same but wages converted to monthly

REQUIREMENTS:
    pip install openpyxl xlrd==1.2.0
    (xlrd 1.2.0 is required for the old .xls files from 2005–2012;
     newer xlrd versions dropped .xls support)
"""

import os
import csv
import io
import zipfile
from pathlib import Path

# ── CONFIGURE THIS ────────────────────────────────────────────────────────────
# Folder where you saved the downloaded zip files.
# Change this to wherever you put them.
ZIPS_DIR = Path(r"C:\Users\Vanilla\Downloads\oews_zips")
# ─────────────────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("./outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Target years ──────────────────────────────────────────────────────────────
# These match the years used in the housing viz.
# BLS OEWS is released annually (May survey); year = survey year.
# Note: 2020 data exists but is lower quality due to pandemic disruptions.
YEARS = [2005, 2009, 2012, 2015, 2019, 2021, 2022, 2023]

# ── Target occupations ────────────────────────────────────────────────────────
# Format: { label, soc_2018, soc_2010, tier, description }
# soc_2018: SOC code used from 2019 onward (2018 SOC revision)
# soc_2010: SOC code used for 2012–2018 data (2010 SOC)
# For years before 2012, BLS used earlier SOC codes — noted in fallbacks below.
# tier: 'red' = can't afford, 'yellow' = priced out by 2022, 'green' = still possible

OCCUPATIONS = [
    {
        "label":       "Home Health Aide",
        # 31-1121 = Home Health & Personal Care Aides (2018 SOC combined code)
        # 31-1011 = Home Health Aides (pre-2018)
        # 31-1120 = aggregate code sometimes used in metro files
        "soc_2018":    "31-1121",
        "soc_2010":    "31-1011",
        "soc_pre2010": "31-1011",
        "soc_extras":  ["31-1120", "31-1100", "31-1122"],
        "tier":        "red",
        "description": "Personal care & home health — lowest-wage essential workers",
    },
    {
        "label":       "Childcare Worker",
        "soc_2018":    "39-9011",
        "soc_2010":    "39-9011",
        "soc_pre2010": "39-9011",
        "soc_extras":  [],
        "tier":        "red",
        "description": "Childcare center and family daycare workers",
    },
    {
        "label":       "Restaurant / Food Service",
        # 35-3023 = Fast Food & Counter Workers (2018 SOC)
        # 35-3021 = Combined Food Prep & Serving (2010 SOC)
        # 35-3000 = aggregate sometimes used
        "soc_2018":    "35-3023",
        "soc_2010":    "35-3021",
        "soc_pre2010": "35-3021",
        "soc_extras":  ["35-3000", "35-3022"],
        "tier":        "red",
        "description": "Boston's second-largest employer sector",
    },
    {
        "label":       "Elementary School Teacher",
        "soc_2018":    "25-2021",
        "soc_2010":    "25-2021",
        "soc_pre2010": "25-2021",
        "soc_extras":  [],
        "tier":        "yellow",
        "description": "BPS and metro-area public/private elementary teachers",
    },
    {
        "label":       "Bus / Transit Driver",
        # 53-3052 = Bus Drivers, Transit & Intercity (2018 SOC)
        # 53-3021 = Bus Drivers (2010 SOC)
        "soc_2018":    "53-3052",
        "soc_2010":    "53-3021",
        "soc_pre2010": "53-3021",
        "soc_extras":  ["53-3050"],
        "tier":        "yellow",
        "description": "MBTA operators and regional transit drivers",
    },
    {
        "label":       "Firefighter",
        "soc_2018":    "33-2011",
        "soc_2010":    "33-2011",
        "soc_pre2010": "33-2011",
        "soc_extras":  [],
        "tier":        "yellow",
        "description": "Municipal firefighters",
    },
    {
        "label":       "Registered Nurse",
        # 29-1141 = Registered Nurses (stable across revisions)
        # 29-1111 = used in some older vintages
        "soc_2018":    "29-1141",
        "soc_2010":    "29-1141",
        "soc_pre2010": "29-1111",
        "soc_extras":  ["29-1110"],
        "tier":        "yellow",
        "description": "Boston's largest sector; wide internal range",
    },
    {
        "label":       "Software Developer",
        # 15-1252 = Software Developers (2018 SOC)
        # 15-1132 = Software Developers, Applications (2010 SOC)
        # 15-1133 = Software Developers, Systems (2010 SOC — sometimes separate)
        # 15-1031 = Computer Software Engineers, Applications (pre-2010)
        # 15-1021 = Computer Programmers (broader fallback)
        "soc_2018":    "15-1252",
        "soc_2010":    "15-1132",
        "soc_pre2010": "15-1031",
        "soc_extras":  ["15-1133", "15-1021", "15-1253", "15-1250", "15-1110"],
        "tier":        "green",
        "description": "Shows what still works in today's market",
    },
]

# All SOC codes we'll look for (to build a single lookup set)
ALL_SOC = set()
for occ in OCCUPATIONS:
    ALL_SOC.update([occ["soc_2018"], occ["soc_2010"], occ["soc_pre2010"]])

# ── Boston MSA area codes (FIPS) ──────────────────────────────────────────────
# BLS changed the Boston metro definition in 2013 (OMB 2013 delineations).
# Pre-2013 files use a different area code for the same metro.
BOSTON_AREA_CODES = {
    # year: [primary_code, fallback_codes...]
    # Older files (pre-2013) sometimes use 7-digit FIPS or different padding
    2005: ["71650", "14460", "0071650", "0014460", "71654"],
    2009: ["71650", "14460", "0071650", "0014460"],
    2012: ["71650", "14460", "0071650", "0014460"],
    2015: ["14460", "71650", "0014460", "0071650"],
    2019: ["14460", "71650", "0014460", "0071650"],
    2021: ["14460", "71650", "0014460", "0071650"],
    2022: ["14460", "71650", "0014460", "0071650"],
    2023: ["14460", "71650", "0014460", "0071650"],
}

# ── Local zip file lookup ─────────────────────────────────────────────────────
def find_local_zip(year):
    """
    Look for the downloaded zip in ZIPS_DIR.
    Accepts the exact BLS filename (oesm05ma.zip) or any file containing
    the year string in case the browser renamed it on download.
    """
    yy       = str(year)[2:]
    expected = ZIPS_DIR / f"oesm{yy}ma.zip"
    if expected.exists():
        return expected

    # Fuzzy fallback — browser may have renamed file
    if ZIPS_DIR.exists():
        for f in ZIPS_DIR.iterdir():
            name = f.name.lower()
            if f.suffix == '.zip' and (f"oesm{yy}" in name or str(year) in name):
                print(f"  {year}: found as {f.name}")
                return f

    print(f"  {year}: zip not found in {ZIPS_DIR}")
    print(f"         Expected: oesm{yy}ma.zip")
    print(f"         Download from: https://www.bls.gov/oes/special.requests/oesm{yy}ma.zip")
    return None

# ── Find the data file inside the zip ────────────────────────────────────────
def find_data_file(zf):
    """Return the name of the metro-area data file inside the zip."""
    names = zf.namelist()

    def is_usable(name):
        # Get just the filename part (strip any folder prefix)
        base = name.replace("\\", "/").split("/")[-1]
        if base.startswith("~$"):    # Excel temp/lock file
            return False
        if base.startswith("."):     # hidden file
            return False
        if base.startswith("__"):    # macOS metadata
            return False
        return True

    # Prefer MSA/metro all-areas file that is NOT a temp file
    for name in names:
        if not is_usable(name):
            continue
        n = name.lower()
        base = n.replace("\\", "/").split("/")[-1]
        if ("msa" in base or "metro" in base or "ma_m" in base) and (
            base.endswith(".xlsx") or base.endswith(".xls") or base.endswith(".csv")
        ):
            return name

    # Fallback: any xlsx/xls/csv not named glossary/layout
    for name in names:
        if not is_usable(name):
            continue
        n = name.lower()
        base = n.replace("\\", "/").split("/")[-1]
        if (base.endswith(".xlsx") or base.endswith(".xls") or base.endswith(".csv")) \
                and "glossary" not in base and "layout" not in base:
            return name
    return None

# ── Parse the data file ───────────────────────────────────────────────────────
def parse_oews_file(zf, filename, year):
    """
    Read the OEWS metro area file and return a dict:
      { (area_code, soc_code): annual_median_wage }
    """
    data = {}
    raw = zf.read(filename)

    if filename.lower().endswith(".csv"):
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8", errors="replace")))
        for row in reader:
            area = str(row.get("AREA", row.get("area", ""))).strip().zfill(5)
            occ  = str(row.get("OCC_CODE", row.get("occ_code", ""))).strip()
            wage = str(row.get("A_MEDIAN", row.get("a_median", ""))).strip()
            if area and occ and wage not in ("*", "#", "", "**"):
                try:
                    data[(area, occ)] = int(float(wage))
                except ValueError:
                    pass
        return data

    # Excel file
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
    except Exception as e:
        print(f"    openpyxl failed ({e}) — trying xlrd")
        try:
            import xlrd
            wb = xlrd.open_workbook(file_contents=raw)
            ws = wb.sheet_by_index(0)
            rows = [ws.row_values(i) for i in range(ws.nrows)]
        except Exception as e2:
            print(f"    xlrd also failed: {e2}")
            return data

    # Find header row
    header = None
    header_idx = 0
    for i, row in enumerate(rows[:10]):
        row_str = [str(c).strip().upper() for c in row]
        if "AREA" in row_str and "OCC_CODE" in row_str:
            header = row_str
            header_idx = i
            break

    if not header:
        print(f"    Could not find header row in {filename}")
        return data

    try:
        area_col   = header.index("AREA")
        occ_col    = header.index("OCC_CODE")
        # A_MEDIAN column
        med_col = None
        for name in ["A_MEDIAN", "ANN_MEDIAN", "ANNUAL_MEDIAN"]:
            if name in header:
                med_col = header.index(name)
                break
        if med_col is None:
            print(f"    No A_MEDIAN column found. Headers: {header}")
            return data
    except ValueError as e:
        print(f"    Header parse error: {e}")
        return data

    for row in rows[header_idx + 1:]:
        if not row or len(row) <= max(area_col, occ_col, med_col):
            continue
        area_raw = str(row[area_col]).strip()
        # Strip trailing .0 from numeric area codes (xlrd returns floats)
        if area_raw.endswith(".0"):
            area_raw = area_raw[:-2]
        # Normalise to 5-digit string — older files use 7-digit FIPS (e.g. 0071650)
        # We store both the raw and the last-5-digits version
        area5 = area_raw.zfill(5)[-5:]   # last 5 digits always
        area7 = area_raw.zfill(7)         # full 7-digit form

        occ  = str(row[occ_col]).strip()
        wage = str(row[med_col]).strip()

        if area5 and occ and wage not in ("*", "#", "", "**", "None"):
            try:
                w = int(float(wage))
                data[(area5, occ)] = w
                if area7 != area5:
                    data[(area7, occ)] = w   # also store 7-digit key as fallback
            except ValueError:
                pass

    # Diagnostic sample: print a few area codes actually found
    if data:
        sample_areas = sorted(set(k[0] for k in list(data.keys())[:200]))[:8]
        print(f"    Sample area codes: {sample_areas}")

    return data

# ── Match occupation to wage in a year's data ────────────────────────────────
def get_wage(parsed, year, occ_def, boston_codes):
    """Try all area code + SOC code combinations for this year."""
    # Build ordered list of SOC codes to try
    if year >= 2019:
        soc_codes = [occ_def["soc_2018"], occ_def["soc_2010"]]
    elif year >= 2012:
        soc_codes = [occ_def["soc_2010"], occ_def["soc_2018"]]
    else:
        soc_codes = [occ_def["soc_pre2010"], occ_def["soc_2010"], occ_def["soc_2018"]]

    # Append any extra fallback codes (deduped)
    for extra in occ_def.get("soc_extras", []):
        if extra not in soc_codes:
            soc_codes.append(extra)

    for area in boston_codes:
        for soc in soc_codes:
            key = (area, soc)
            if key in parsed:
                return parsed[key], area, soc

    return None, None, None

# ── Main ─────────────────────────────────────────────────────────────────────
print("BLS OEWS — Boston MSA Occupation Wage Extraction")
print("=" * 52)
print(f"Looking for zip files in: {ZIPS_DIR}")
if not ZIPS_DIR.exists():
    print(f"\nERROR: Folder not found: {ZIPS_DIR}")
    print("Create the folder, download the zip files into it, then re-run.")
    print("\nDownload URLs (paste each into your browser):")
    for y in YEARS:
        yy = str(y)[2:]
        print(f"  https://www.bls.gov/oes/special.requests/oesm{yy}ma.zip")
    exit(1)
print()

results = []  # list of dicts

for year in YEARS:
    print(f"── {year} ──────────────────────────────────────────")
    zip_path = find_local_zip(year)
    if not zip_path:
        print(f"  Skipping {year} — no data file")
        continue

    # Parse ALL eligible data files in the zip and merge into one dict.
    # Older years (2009, 2012) split data across multiple regional files —
    # we scan all of them so Boston is found regardless of which split it's in.
    parsed = {}
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()

            def is_data_file(name):
                base = name.replace("\\", "/").split("/")[-1].lower()
                if base.startswith("~$") or base.startswith(".") or base.startswith("__"):
                    return False
                if "glossary" in base or "layout" in base or "readme" in base:
                    return False
                return base.endswith(".xlsx") or base.endswith(".xls") or base.endswith(".csv")

            data_files = [n for n in names if is_data_file(n)]

            if not data_files:
                print(f"  No data files found. Contents: {names}")
                continue

            print(f"  Found {len(data_files)} data file(s) in zip")
            for df in data_files:
                print(f"  Parsing: {df}")
                chunk = parse_oews_file(zf, df, year)
                # Only merge if this file contains Boston or we haven't found it yet
                boston_codes = BOSTON_AREA_CODES.get(year, ["14460", "71650"])
                has_boston = any(k[0] in boston_codes for k in chunk)
                if has_boston or not parsed:
                    parsed.update(chunk)
                    if has_boston:
                        print(f"    ✓ Boston data found in this file ({len(chunk):,} records)")
                        break  # stop scanning once we have Boston
                else:
                    print(f"    — Boston not in this file, skipping merge")

            print(f"  Total loaded: {len(parsed):,} (area, occ) records")

    except Exception as e:
        print(f"  Failed to read zip: {e}")
        continue

    boston_codes = BOSTON_AREA_CODES.get(year, ["14460", "71650"])

    for occ in OCCUPATIONS:
        wage, matched_area, matched_soc = get_wage(parsed, year, occ, boston_codes)
        status = "✓" if wage else "—"
        wage_str = f"${wage:,}" if wage else "N/A"
        print(f"  {status} {occ['label']:<28} {wage_str:>10}  "
              f"(area={matched_area}, soc={matched_soc})")

        # Diagnostic: when N/A, show which SOC codes for this occ exist in any area
        if not wage and parsed:
            all_socs = [occ["soc_2018"], occ["soc_2010"], occ["soc_pre2010"]] \
                       + occ.get("soc_extras", [])
            found = [(a, s, w) for (a, s), w in parsed.items()
                     if s in all_socs]
            if found:
                for a, s, w in found[:3]:
                    print(f"       → found soc={s} in area={a} (${w:,}) — not a Boston code")
            else:
                print(f"       → SOC codes {all_socs} not found in any area")

        results.append({
            "year":          year,
            "occupation":    occ["label"],
            "tier":          occ["tier"],
            "soc_matched":   matched_soc or "",
            "area_matched":  matched_area or "",
            "annual_wage":   wage,
            "monthly_wage":  round(wage / 12) if wage else None,
            "description":   occ["description"],
            "source":        "BLS OEWS, Boston-Cambridge-Nashua MSA",
            "data_status":   "confirmed" if wage else "suppressed",
        })
    print()

# ── Post-process: interpolate suppressed values ───────────────────────────────
# When BLS suppresses a value, interpolate linearly from nearest confirmed years.
# Flagged as "estimated" in data_status so the viz can show uncertainty.

print("Checking for suppressions to interpolate...")

# Build mutable lookup: (occ_label, year) -> result dict
result_map = {(r["occupation"], r["year"]): r for r in results}

for occ in OCCUPATIONS:
    label = occ["label"]
    occ_rows = sorted(
        [r for r in results if r["occupation"] == label and r["annual_wage"] is not None],
        key=lambda r: r["year"]
    )
    confirmed_years = {r["year"]: r["annual_wage"] for r in occ_rows}

    for year in YEARS:
        key = (label, year)
        if key not in result_map:
            continue
        row = result_map[key]
        if row["annual_wage"] is not None:
            continue  # already confirmed

        # Find nearest confirmed values before and after
        before = [(y, w) for y, w in confirmed_years.items() if y < year]
        after  = [(y, w) for y, w in confirmed_years.items() if y > year]

        if before and after:
            y0, w0 = max(before, key=lambda x: x[0])
            y1, w1 = min(after,  key=lambda x: x[0])
            t = (year - y0) / (y1 - y0)
            interp = round(w0 + (w1 - w0) * t)
            row["annual_wage"]  = interp
            row["monthly_wage"] = round(interp / 12)
            row["data_status"]  = f"estimated (interpolated {y0}–{y1})"
            row["soc_matched"]  = "interpolated"
            print(f"  ✦ Interpolated {label} {year}: ${interp:,}/yr  (from {y0}=${w0:,} → {y1}=${w1:,})")
        elif after:
            y1, w1 = min(after, key=lambda x: x[0])
            row["annual_wage"]  = w1
            row["monthly_wage"] = round(w1 / 12)
            row["data_status"]  = f"estimated (carried from {y1})"
            row["soc_matched"]  = "estimated"
            print(f"  ✦ Carried back {label} {year}: ${w1:,}/yr  (from {y1})")
        else:
            print(f"  ✗ Cannot interpolate {label} {year} — no confirmed values on either side")

print()

# ── Write long-format CSV ─────────────────────────────────────────────────────
if not results:
    print("\nNo data extracted — make sure the zip files are in ZIPS_DIR and re-run.")
    exit(1)

long_path = OUTPUT_DIR / "oews_boston_occupations.csv"
with open(long_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
print(f"Wrote {len(results)} rows → {long_path}")

# ── Write wide-format CSV (occupations as rows, years as columns) ─────────────
occ_labels = [o["label"] for o in OCCUPATIONS]
wide_path  = OUTPUT_DIR / "oews_boston_wide.csv"
monthly_path = OUTPUT_DIR / "oews_boston_monthly.csv"

# Build lookup
wage_lookup = {}
for r in results:
    wage_lookup[(r["occupation"], r["year"])] = r["annual_wage"]
monthly_lookup = {}
for r in results:
    monthly_lookup[(r["occupation"], r["year"])] = r["monthly_wage"]

with open(wide_path, "w", newline="") as f, \
     open(monthly_path, "w", newline="") as fm:

    cols = ["occupation", "tier"] + [str(y) for y in YEARS]
    wr  = csv.writer(f)
    wrm = csv.writer(fm)
    wr.writerow(cols)
    wrm.writerow(cols)

    for occ in OCCUPATIONS:
        row = [occ["label"], occ["tier"]]
        row_m = [occ["label"], occ["tier"]]
        for year in YEARS:
            row.append(wage_lookup.get((occ["label"], year), ""))
            row_m.append(monthly_lookup.get((occ["label"], year), ""))
        wr.writerow(row)
        wrm.writerow(row_m)

print(f"Wrote wide format   → {wide_path}")
print(f"Wrote monthly wages → {monthly_path}")

# ── Summary table ─────────────────────────────────────────────────────────────
# Build status lookup for display
status_lookup = {(r["occupation"], r["year"]): r["data_status"] for r in results}

print()
print("=" * 72)
print("SUMMARY — Boston MSA Annual Median Wages by Occupation")
print("  ~ = estimated/interpolated, N/A = suppressed/unavailable")
print("=" * 72)
print(f"  {'Occupation':<28} {'Tier':<8}", end="")
for y in YEARS:
    print(f"  {y}", end="")
print()
print("-" * 72)

for occ in OCCUPATIONS:
    print(f"  {occ['label']:<28} {occ['tier']:<8}", end="")
    for year in YEARS:
        w = wage_lookup.get((occ["label"], year))
        st = status_lookup.get((occ["label"], year), "")
        is_est = "estimated" in str(st)
        if not w:
            cell = "N/A"
        elif is_est:
            cell = "~$" + str(w // 1000) + "K"
        else:
            cell = "$" + str(w // 1000) + "K"
        print(f"  {cell:>7}", end="")
    print()

print()
print("NOTE: All wages nominal (not inflation-adjusted).")
print("NOTE: SOC codes changed with 2018 revision — see soc_matched column.")
print("NOTE: 2020 excluded — BLS OEWS disrupted by pandemic data collection.")
print()
print("Files written to:", OUTPUT_DIR.resolve())