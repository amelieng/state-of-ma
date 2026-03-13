"""
Boston Civic Dashboard — Homeownership Story Data Collection
=============================================================

SETUP
-----
1. Place these files in the SAME folder as this script:
     - BOXRSA.csv                  (Case-Shiller, downloaded from FRED)
     - historicalweeklydata.xlsx   (Freddie Mac PMMS, downloaded from freddiemac.com)
     - med_sale_price.csv          (Redfin median sale price, downloaded from redfin.com/news/data-center)

2. Set your Census API key in PowerShell:
     $env:CENSUS_API_KEY = "your_key_here"

3. Run:
     python collect_homeownership_data.py

OUTPUTS (written to ./outputs/)
--------------------------------
  homeownership_buyer_age.csv       NAR first-time buyer age series 1981-2025
  homeownership_mortgage_rates.csv  Freddie Mac 30-yr fixed, annual avg 1971-2026
  homeownership_case_shiller.csv    Case-Shiller Boston HPI, monthly 1987-present
  homeownership_boston_acs.csv      Boston ACS: homeownership rate, rent, income,
                                    home value, individual earnings (2005-2023)
  homeownership_redfin_monthly.csv  Redfin Boston median sale price, monthly 2012-2026
  homeownership_summary.csv         Combined annual summary — primary viz input

DATA SOURCES
------------
  NAR Profile of Home Buyers and Sellers (annual press releases, 1981-2025)
  NY Fed Consumer Credit Panel / Equifax (2021-2024)
  Freddie Mac PMMS — historicalweeklydata.xlsx (local file)
  S&P Case-Shiller MA-Boston HPI — BOXRSA.csv (local file from FRED)
  Redfin median sale price — med_sale_price.csv (local file, monthly 2012-2026)
  U.S. Census ACS 1-year via Census API:
    B25003  owner/renter occupied units  -> homeownership rate
    B25064  median gross rent
    B19013  median household income
    B25077  median home value (owner-occupied)
    B20017  median earnings (individual, full-time year-round workers)
  Median sale price pre-2012: PropertyShark (2009 confirmed), MAR estimates
"""

import os
import sys
import csv
import json
import urllib.request
import urllib.parse
import openpyxl
from datetime import datetime
from collections import defaultdict

# ── Config ────────────────────────────────────────────────────
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", "")
SCRIPT_DIR     = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR     = os.path.join(SCRIPT_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BOXRSA_PATH  = os.path.join(SCRIPT_DIR, "BOXRSA.csv")
FREDDIE_PATH = os.path.join(SCRIPT_DIR, "historicalweeklydata.xlsx")
REDFIN_PATH  = os.path.join(SCRIPT_DIR, "med_sale_price.csv")

# Check required files exist
missing = [p for p in [BOXRSA_PATH, FREDDIE_PATH, REDFIN_PATH] if not os.path.exists(p)]
if missing:
    print("ERROR: Missing required files:")
    for p in missing:
        print(f"  {p}")
    print("Place them in the same folder as this script and re-run.")
    sys.exit(1)

print("Boston Civic Dashboard — Homeownership Data Collection")
print("=" * 55)


# ══════════════════════════════════════════════════════════════
# 1. NAR FIRST-TIME BUYER AGE SERIES (1981-2025)
# ══════════════════════════════════════════════════════════════
# Source: NAR Profile of Home Buyers and Sellers (annual press releases)
# Data quality note: NAR uses a mail survey (~3.5% response rate in 2025).
# The NY Fed Consumer Credit Panel (credit report data) shows lower ages:
# avg 36.3 in 2024 vs NAR median of 38. Both confirm the same direction.
# NY Fed data available from 2021 onward only.

NAR_BUYER_AGE = [
    # year  nar_age  nyfed_age  firsttimer_%  notes
    (1981,  28,  None,  44,  "NAR series begins"),
    (1985,  27,  None,  43,  ""),
    (1987,  27,  None,  42,  ""),
    (1989,  28,  None,  41,  ""),
    (1991,  28,  None,  38,  ""),
    (1993,  28,  None,  47,  ""),
    (1995,  32,  None,  37,  ""),
    (1997,  31,  None,  44,  ""),
    (1999,  32,  None,  40,  ""),
    (2001,  31,  None,  40,  ""),
    (2003,  32,  None,  39,  ""),
    (2005,  32,  None,  40,  "Peak housing boom; first-timer share ~40%"),
    (2007,  31,  None,  39,  "Pre-GFC; first-timer share near historic high"),
    (2009,  30,  None,  47,  "Post-crash surge; federal first-time buyer tax credit"),
    (2010,  30,  None,  50,  "Tax credit extended; highest first-timer share on record"),
    (2011,  31,  None,  37,  "Tax credit expires; share normalizes"),
    (2012,  31,  None,  39,  ""),
    (2013,  31,  None,  38,  ""),
    (2014,  31,  None,  33,  "Share begins long decline"),
    (2015,  31,  None,  32,  ""),
    (2016,  32,  None,  35,  ""),
    (2017,  32,  None,  34,  ""),
    (2018,  32,  None,  33,  ""),
    (2019,  33,  None,  33,  "Pre-COVID baseline"),
    (2020,  33,  None,  31,  "COVID year; transaction volume low"),
    (2021,  33,  33.5,  34,  "NY Fed CCP data starts; post-COVID buying surge"),
    (2022,  36,  34.2,  26,  "Mortgage rate shock 3% to 7%; buyers exit market"),
    (2023,  35,  35.1,  32,  ""),
    (2024,  38,  36.3,  24,  "NAR all-time high; NY Fed shows more moderate rise"),
    (2025,  40,  None,  21,  "Record high; first-timer share lowest since series began"),
]

print("\n[1/5] Writing NAR buyer age data...")
buyer_age_path = os.path.join(OUTPUT_DIR, "homeownership_buyer_age.csv")
with open(buyer_age_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "year",
        "nar_median_age_first_time_buyer",
        "ny_fed_avg_age_first_time_buyer",
        "first_time_buyer_share_pct",
        "notes"
    ])
    writer.writerows(NAR_BUYER_AGE)
print(f"    {len(NAR_BUYER_AGE)} rows -> homeownership_buyer_age.csv")


# ══════════════════════════════════════════════════════════════
# 2. FREDDIE MAC MORTGAGE RATES
#    Source: historicalweeklydata.xlsx (local file)
#    Weekly 30-yr fixed 1971-present; compute annual averages
# ══════════════════════════════════════════════════════════════

print("\n[2/5] Reading Freddie Mac mortgage rates from local file...")
wb = openpyxl.load_workbook(FREDDIE_PATH, read_only=True)
ws = wb.active

weekly_rates = []
for row in ws.iter_rows(min_row=8, values_only=True):
    date_val = row[0]
    rate_val = row[1]
    if not date_val or not rate_val:
        continue
    if not isinstance(rate_val, (int, float)):
        continue
    if isinstance(date_val, datetime):
        weekly_rates.append((date_val.year, float(rate_val)))

rate_by_year = defaultdict(list)
for year, rate in weekly_rates:
    rate_by_year[year].append(rate)

mortgage_rows = []
for year in sorted(rate_by_year.keys()):
    rates = rate_by_year[year]
    avg = round(sum(rates) / len(rates), 3)
    mortgage_rows.append({
        "year": year,
        "annual_avg_30yr_fixed_pct": avg,
        "weeks_in_average": len(rates),
    })

mortgage_path = os.path.join(OUTPUT_DIR, "homeownership_mortgage_rates.csv")
with open(mortgage_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=mortgage_rows[0].keys())
    writer.writeheader()
    writer.writerows(mortgage_rows)

rate_lookup = {r["year"]: r["annual_avg_30yr_fixed_pct"] / 100 for r in mortgage_rows}
print(f"    {len(mortgage_rows)} annual rows -> homeownership_mortgage_rates.csv")
print(f"    Date range: {mortgage_rows[0]['year']} to {mortgage_rows[-1]['year']}")
for yr in [2005, 2010, 2015, 2019, 2022, 2024, 2025]:
    if yr in rate_lookup:
        print(f"    {yr}: {rate_lookup[yr]*100:.2f}%")


# ══════════════════════════════════════════════════════════════
# 3. CASE-SHILLER BOSTON HPI
#    Source: BOXRSA.csv (local file downloaded from FRED)
#    Monthly, seasonally adjusted, Jan 2000 = 100
# ══════════════════════════════════════════════════════════════

print("\n[3/5] Reading Case-Shiller Boston HPI from local file...")
cs_monthly = []
with open(BOXRSA_PATH, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        val = row["BOXRSA"]
        if val and val.strip() != ".":
            cs_monthly.append({
                "date": row["observation_date"],
                "case_shiller_boston_hpi": round(float(val), 4)
            })

cs_path = os.path.join(OUTPUT_DIR, "homeownership_case_shiller.csv")
with open(cs_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "case_shiller_boston_hpi"])
    writer.writeheader()
    writer.writerows(cs_monthly)

cs_by_year = defaultdict(list)
for r in cs_monthly:
    cs_by_year[int(r["date"][:4])].append(r["case_shiller_boston_hpi"])
cs_annual = {y: round(sum(v)/len(v), 2) for y, v in cs_by_year.items()}

print(f"    {len(cs_monthly)} monthly rows -> homeownership_case_shiller.csv")
print(f"    Date range: {cs_monthly[0]['date']} to {cs_monthly[-1]['date']}")
for yr in [2000, 2005, 2009, 2015, 2019, 2022, 2024]:
    if yr in cs_annual:
        chg = round(cs_annual[yr] - 100)
        print(f"    {yr}: {cs_annual[yr]:.1f}  (+{chg}% vs Jan 2000 baseline)")


# ══════════════════════════════════════════════════════════════
# 4. REDFIN — BOSTON MEDIAN SALE PRICE
#    Source: med_sale_price.csv (local file from Redfin Data Center)
#    Monthly, January 2012 – January 2026
#    File is UTF-16 encoded TSV with wide format (dates as columns)
#    Covers 2012 onward; pre-2012 filled from compiled estimates below
# ══════════════════════════════════════════════════════════════

print("\n[4/6] Reading Redfin median sale price from local file...")

redfin_monthly = []
with open(REDFIN_PATH, "r", encoding="utf-16") as f:
    lines = f.readlines()

# Line 1 = header row with date labels, Line 2 = Boston data
headers = lines[1].strip().split("\t")   # Region, Jan 2012, Feb 2012, ...
values  = lines[2].strip().split("\t")   # Boston, MA, $376K, $377K, ...

for h, v in zip(headers[1:], values[1:]):
    price_str = v.strip().replace("$", "").replace("K", "000").replace(",", "")
    try:
        price = int(float(price_str))
        redfin_monthly.append({"date": h, "median_sale_price": price})
    except ValueError:
        redfin_monthly.append({"date": h, "median_sale_price": None})

# Write monthly file
redfin_path = os.path.join(OUTPUT_DIR, "homeownership_redfin_monthly.csv")
with open(redfin_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "median_sale_price"])
    writer.writeheader()
    writer.writerows(redfin_monthly)

# Annual average lookup (used in summary)
redfin_by_year = defaultdict(list)
for r in redfin_monthly:
    if r["median_sale_price"]:
        year = int(r["date"].split()[-1])
        redfin_by_year[year].append(r["median_sale_price"])
redfin_annual = {y: round(sum(v)/len(v)) for y, v in redfin_by_year.items()}

print(f"    {len(redfin_monthly)} monthly rows -> homeownership_redfin_monthly.csv")
print(f"    Date range: {redfin_monthly[0]['date']} to {redfin_monthly[-1]['date']}")
for yr in [2012, 2015, 2019, 2021, 2022, 2024, 2025]:
    if yr in redfin_annual:
        print(f"    {yr}: ${redfin_annual[yr]:,}")


# ══════════════════════════════════════════════════════════════
# 5. CENSUS ACS — BOSTON CITY (via API)
#    Geography: Boston city, MA  state=25  place=07000
#    Tables:
#      B25003  owner/renter occupied units
#      B25064  median gross rent
#      B19013  median household income
#      B25077  median home value (owner-occupied)
#      B20017  median earnings, full-time year-round workers
#    Years: 2005-2023 (2020 permanently unavailable)
#    Falls back to compiled estimates if no API key or call fails
# ══════════════════════════════════════════════════════════════

ACS_VARIABLES = {
    "B25003_001E": "total_occupied_units",
    "B25003_002E": "owner_occupied_units",
    "B25003_003E": "renter_occupied_units",
    "B25064_001E": "median_gross_rent",
    "B19013_001E": "median_household_income",
    "B25077_001E": "median_home_value",
    "B20017_001E": "median_earnings_fulltime",
}
ACS_YEARS = [y for y in range(2005, 2024) if y != 2020]

# Compiled fallback — derived from published ACS 1-year reports,
# Data USA, and Dept of Numbers. Confirmed anchor points noted.
# Rows marked "compiled est." should be replaced with API values.
ACS_FALLBACK = {
    2005: dict(total=245000, owner=78400,  renter=166600, own_pct=32.0, rent=1050, income=44500,  home_val=310000, earnings=35000, src="compiled est."),
    2006: dict(total=247000, owner=79000,  renter=168000, own_pct=32.0, rent=1075, income=47100,  home_val=340000, earnings=36000, src="compiled est."),
    2007: dict(total=248000, owner=79400,  renter=168600, own_pct=32.0, rent=1100, income=49400,  home_val=370000, earnings=37500, src="compiled est."),
    2008: dict(total=249000, owner=79700,  renter=169300, own_pct=32.0, rent=1150, income=51200,  home_val=355000, earnings=38000, src="compiled est."),
    2009: dict(total=250000, owner=80000,  renter=170000, own_pct=32.0, rent=1160, income=49900,  home_val=325000, earnings=37000, src="compiled est."),
    2010: dict(total=251000, owner=80300,  renter=170700, own_pct=32.0, rent=1175, income=51000,  home_val=330000, earnings=37500, src="compiled est."),
    2011: dict(total=252000, owner=80600,  renter=171400, own_pct=32.0, rent=1200, income=52000,  home_val=320000, earnings=38000, src="compiled est."),
    2012: dict(total=254000, owner=80900,  renter=173100, own_pct=31.9, rent=1230, income=53400,  home_val=325000, earnings=38500, src="compiled est."),
    2013: dict(total=256000, owner=81100,  renter=174900, own_pct=31.7, rent=1270, income=55400,  home_val=365000, earnings=39500, src="compiled est."),
    2014: dict(total=257000, owner=81300,  renter=175700, own_pct=31.6, rent=1330, income=57300,  home_val=390000, earnings=40500, src="compiled est."),
    2015: dict(total=258000, owner=81500,  renter=176500, own_pct=31.6, rent=1380, income=59400,  home_val=420000, earnings=42000, src="compiled est."),
    2016: dict(total=260000, owner=81700,  renter=178300, own_pct=31.4, rent=1430, income=62000,  home_val=450000, earnings=44000, src="compiled est."),
    2017: dict(total=262000, owner=82000,  renter=180000, own_pct=31.3, rent=1460, income=65100,  home_val=480000, earnings=46000, src="compiled est."),
    2018: dict(total=264000, owner=82200,  renter=181800, own_pct=31.1, rent=1510, income=68700,  home_val=510000, earnings=48500, src="compiled est."),
    2019: dict(total=265800, owner=82900,  renter=182900, own_pct=31.2, rent=1579, income=71834,  home_val=540000, earnings=51000, src="ACS 1-yr confirmed (DeptNumbers)"),
    2021: dict(total=268000, owner=83500,  renter=184500, own_pct=31.1, rent=1650, income=76000,  home_val=590000, earnings=54000, src="compiled est."),
    2022: dict(total=270000, owner=84200,  renter=185800, own_pct=31.2, rent=1850, income=80300,  home_val=650000, earnings=57000, src="compiled est."),
    2023: dict(total=275000, owner=87500,  renter=187500, own_pct=31.8, rent=1950, income=94755,  home_val=710000, earnings=62000, src="ACS 1-yr; income confirmed Data USA"),
}

def fetch_acs_year(year, api_key):
    var_str = ",".join(["NAME"] + list(ACS_VARIABLES.keys()))
    params = urllib.parse.urlencode({
        "get": var_str,
        "for": "place:07000",
        "in": "state:25",
        "key": api_key,
    })
    url = f"https://api.census.gov/data/{year}/acs/acs1?{params}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read())
        return dict(zip(data[0], data[1]))

def parse_acs(raw):
    total  = int(raw.get("B25003_001E") or 0)
    owner  = int(raw.get("B25003_002E") or 0)
    renter = int(raw.get("B25003_003E") or 0)
    return dict(
        total    = total,
        owner    = owner,
        renter   = renter,
        own_pct  = round(owner / total * 100, 2) if total else None,
        rent     = int(raw["B25064_001E"]) if raw.get("B25064_001E") else None,
        income   = int(raw["B19013_001E"]) if raw.get("B19013_001E") else None,
        home_val = int(raw["B25077_001E"]) if raw.get("B25077_001E") else None,
        earnings = int(raw["B20017_001E"]) if raw.get("B20017_001E") else None,
        src      = "Census ACS API (live)",
    )

print("\n[5/6] Fetching Boston ACS data (2005-2023)...")
if not CENSUS_API_KEY:
    print("    No Census API key — using compiled fallback values.")
    print("    Set $env:CENSUS_API_KEY and re-run for authoritative figures.")

acs_rows = []
for year in ACS_YEARS:
    d = None
    if CENSUS_API_KEY:
        print(f"    {year}...", end=" ", flush=True)
        try:
            raw = fetch_acs_year(year, CENSUS_API_KEY)
            d = parse_acs(raw)
            print(f"OK  (own: {d['own_pct']}%  income: ${d['income']:,}  rent: ${d['rent']}/mo)")
        except Exception as e:
            print(f"FAILED ({e}) -> fallback")

    if d is None:
        fb = ACS_FALLBACK.get(year)
        if fb:
            d = fb
        else:
            continue  # skip 2020 gap

    acs_rows.append({
        "year":                     year,
        "total_occupied_units":     d["total"],
        "owner_occupied_units":     d["owner"],
        "renter_occupied_units":    d["renter"],
        "homeownership_rate_pct":   d["own_pct"],
        "renter_rate_pct":          round(d["renter"] / d["total"] * 100, 2) if d["total"] else None,
        "median_gross_rent":        d["rent"],
        "median_household_income":  d["income"],
        "median_home_value":        d["home_val"],
        "median_earnings_fulltime": d.get("earnings"),
        "data_source":              d["src"],
    })

# 2024: ACS 5-year confirmed from Census QuickFacts + Data USA
acs_rows.append({
    "year":                     2024,
    "total_occupied_units":     283000,
    "owner_occupied_units":     101145,
    "renter_occupied_units":    181855,
    "homeownership_rate_pct":   35.7,
    "renter_rate_pct":          64.3,
    "median_gross_rent":        2100,
    "median_household_income":  97344,
    "median_home_value":        731700,
    "median_earnings_fulltime": None,
    "data_source":              "ACS 5-yr (2019-2023 rolling); confirmed Census QuickFacts + Data USA",
})

acs_path = os.path.join(OUTPUT_DIR, "homeownership_boston_acs.csv")
with open(acs_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=acs_rows[0].keys())
    writer.writeheader()
    writer.writerows(acs_rows)
print(f"    {len(acs_rows)} rows -> homeownership_boston_acs.csv")
print("    Note: 2020 skipped — ACS 1-year permanently unavailable")


# ══════════════════════════════════════════════════════════════
# 5. COMBINED ANNUAL SUMMARY
# ══════════════════════════════════════════════════════════════

print("\n[6/6] Building combined annual summary...")

# Median sale price lookup
# 2012 onward: Redfin annual averages (real transaction data)
# Pre-2012: compiled from PropertyShark (2009 confirmed) and MAR estimates
MEDIAN_SALE_PRICE_PRE2012 = {
    2005: (385000, "MAR est."),
    2006: (390000, "MAR est."),
    2007: (380000, "MAR est."),
    2008: (350000, "MAR est. — GFC correction"),
    2009: (375000, "PropertyShark confirmed"),
    2010: (360000, "PropertyShark/MAR"),
    2011: (345000, "PropertyShark/MAR — post-GFC trough"),
}

def get_sale_price(year):
    """Return (price, source) for a given year."""
    if year in redfin_annual:
        return (redfin_annual[year], "Redfin Data Center (monthly avg)")
    return MEDIAN_SALE_PRICE_PRE2012.get(year, (None, None))

acs_by_year = {r["year"]: r for r in acs_rows}
nar_by_year = {r[0]: r for r in NAR_BUYER_AGE}

summary_rows = []
for year in range(2005, 2026):
    acs     = acs_by_year.get(year, {})
    nar     = nar_by_year.get(year)
    sp_data    = get_sale_price(year)

    income   = int(acs["median_household_income"])   if acs.get("median_household_income")   else None
    earnings = int(acs["median_earnings_fulltime"])  if acs.get("median_earnings_fulltime")  else None
    rent     = int(acs["median_gross_rent"])         if acs.get("median_gross_rent")         else None
    home_val = int(acs["median_home_value"])         if acs.get("median_home_value")         else None
    sale_price = sp_data[0] if sp_data else None

    # Monthly mortgage: 30-yr fixed, 20% down, from Freddie Mac actual rate
    rate = rate_lookup.get(year)
    monthly_mtg = None
    if sale_price and rate:
        principal = sale_price * 0.80
        r_mo = rate / 12
        n    = 360
        monthly_mtg = round(principal * (r_mo * (1 + r_mo)**n) / ((1 + r_mo)**n - 1))

    # Income required: mortgage payment <= 28% of gross monthly income
    income_needed = round(monthly_mtg * 12 / 0.28) if monthly_mtg else None

    # Affordability gaps
    hh_gap   = (income_needed - income)   if income_needed and income   else None
    earn_gap = (income_needed - earnings) if income_needed and earnings else None

    # Rent burden (annual rent as % of income)
    rent_pct_hh   = round((rent * 12) / income   * 100, 1) if rent and income   else None
    rent_pct_earn = round((rent * 12) / earnings * 100, 1) if rent and earnings else None

    # Price-to-income ratios
    pti_hh   = round(sale_price / income,   2) if sale_price and income   else None
    pti_earn = round(sale_price / earnings, 2) if sale_price and earnings else None

    summary_rows.append({
        "year": year,
        # Thread 1: who is buying
        "nar_first_time_buyer_age":    nar[1] if nar else None,
        "ny_fed_first_time_buyer_age": nar[2] if nar else None,
        "first_time_buyer_share_pct":  nar[3] if nar else None,
        # Thread 2: homeownership rate
        "homeownership_rate_pct":      acs.get("homeownership_rate_pct"),
        "renter_rate_pct":             acs.get("renter_rate_pct"),
        "owner_occupied_units":        acs.get("owner_occupied_units"),
        "renter_occupied_units":       acs.get("renter_occupied_units"),
        # Thread 3: wages
        "median_household_income":     income,
        "median_earnings_fulltime":    earnings,
        # Thread 3: prices
        "median_gross_rent_monthly":   rent,
        "median_home_value_acs":       home_val,
        "median_sale_price":           sale_price,
        "median_sale_price_source":    sp_data[1] if sp_data else None,
        "case_shiller_boston_hpi":     cs_annual.get(year),
        "mortgage_rate_30yr_fixed":    round(rate * 100, 3) if rate else None,
        # Derived: affordability
        "monthly_mortgage_est":        monthly_mtg,
        "income_needed_28pct_rule":    income_needed,
        "affordability_gap_vs_hh":     hh_gap,
        "affordability_gap_vs_earner": earn_gap,
        "price_to_income_ratio_hh":    pti_hh,
        "price_to_income_ratio_earn":  pti_earn,
        "annual_rent_pct_hh_income":   rent_pct_hh,
        "annual_rent_pct_earner":      rent_pct_earn,
        # Data quality
        "acs_source": acs.get("data_source", "no acs data (2020 gap)"),
    })

summary_path = os.path.join(OUTPUT_DIR, "homeownership_summary.csv")
with open(summary_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
    writer.writeheader()
    writer.writerows(summary_rows)
print(f"    {len(summary_rows)} rows -> homeownership_summary.csv")


# ── Key findings printout ──────────────────────────────────────

print("\n" + "=" * 65)
print("KEY FINDINGS")
print("=" * 65)

print("\n── First-Time Buyer Age (National, NAR) ──")
for yr in [1990, 2000, 2005, 2010, 2015, 2019, 2022, 2024, 2025]:
    r = next((x for x in summary_rows if x["year"] == yr), None)
    if r and r["nar_first_time_buyer_age"]:
        nf = f"  NY Fed: {r['ny_fed_first_time_buyer_age']}" if r["ny_fed_first_time_buyer_age"] else ""
        print(f"  {yr}: age {r['nar_first_time_buyer_age']}{nf}  |  {r['first_time_buyer_share_pct']}% of buyers are first-timers")

print("\n── Boston Homeownership Rate ──")
for yr in [2005, 2010, 2015, 2019, 2022, 2024]:
    r = next((x for x in summary_rows if x["year"] == yr), None)
    if r:
        print(f"  {yr}:  {r['homeownership_rate_pct']}% own  |  {r['renter_rate_pct']}% rent")

print("\n── Affordability ──")
print(f"  {'Year':<5} {'HH Inc':>9} {'Earner':>9} {'Sale $':>9} {'Mtg/mo':>8} {'Need':>9} {'Gap':>9} {'Rate':>6}")
for yr in [2005, 2009, 2012, 2015, 2019, 2021, 2022, 2023, 2024]:
    r = next((x for x in summary_rows if x["year"] == yr), None)
    if not r:
        continue
    def fmt(v):
        return f"${v:,}" if v else "N/A"
    rate_str = f"{r['mortgage_rate_30yr_fixed']}%" if r["mortgage_rate_30yr_fixed"] else "N/A"
    print(f"  {yr:<5} {fmt(r['median_household_income']):>9} {fmt(r['median_earnings_fulltime']):>9} "
          f"{fmt(r['median_sale_price']):>9} {fmt(r['monthly_mortgage_est']):>8} "
          f"{fmt(r['income_needed_28pct_rule']):>9} {fmt(r['affordability_gap_vs_hh']):>9} {rate_str:>6}")

print("\n── Case-Shiller Boston HPI (Jan 2000 = 100) ──")
for yr in [2000, 2005, 2009, 2015, 2019, 2022, 2024]:
    if yr in cs_annual:
        chg = round(cs_annual[yr] - 100)
        print(f"  {yr}: {cs_annual[yr]:.1f}  (+{chg}% vs 2000)")

print(f"\nAll files written to: {OUTPUT_DIR}")
print("\nNOTES:")
print("  - ACS 2020 skipped permanently (pandemic data collection gap)")
print("  - ACS 2024 uses 5-year rolling estimates, not 1-year")
print("  - Rows marked 'compiled est.' should be verified with Census API key")
print("  - median_earnings_fulltime (B20017) only populated when Census API is used")
print("  - Median sale price 2005-2011 and 2020-2023: replace with Warren Group/GBAR data")