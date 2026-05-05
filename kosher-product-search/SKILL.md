---
name: "kosher-product-search"
description: "Search Orthodox Union (OU), OK Kosher, and STAR-K certification listings. Use when the user asks to find, verify, compare, or interpret kosher product records, company listings, certification status, symbols, dairy/pareve/meat designation, Passover status, company/brand listings, K-ID records, STAR-K record IDs, or whether a product appears in kosher agency databases."
---

# Kosher Product Search

## Quick Start

Use the bundled scripts for repeatable searches:

```bash
SKILL_DIR="$HOME/.codex/skills/kosher-product-search"
python3 "$SKILL_DIR/scripts/search_ou_products.py" "tuna burger" --exact
python3 "$SKILL_DIR/scripts/search_ok_products.py" "matcha" --limit 25
python3 "$SKILL_DIR/scripts/search_stark_products.py" "pizza" --limit 25
```

If the skill is installed in another runtime, set `SKILL_DIR` to that installed folder.

The OU script calls:

```text
https://productsearch-v2.oukosher.org/api/v1/product?page=1&limit=50&query=<query>
```

The OK script parses the public product-search results page:

```text
https://www.ok.org/product-search/?term=<query>
```

The STAR-K script parses the public listings page:

```text
https://www.star-k.org/listings?section=<star-k|star-d|star-s>&q=<query>
```

All bundled scripts use only Python standard library modules. If network access is blocked by sandboxing, rerun the same command with the appropriate approval/escalation.

## Workflow

1. Pick the agency source:
   - Use `search_ou_products.py` for OU records.
   - Use `search_ok_products.py` for OK records or when the user links to `ok.org/product-search`.
   - Use `search_stark_products.py` for STAR-K company/category listings or when the user links to `star-k.org/listings`.
2. Search broadly with the product name, UPC, brand, company, OU agency ID, OK K-ID, or STAR-K record ID.
3. For OK searches, pass either a search term or the full OK search URL, such as `https://www.ok.org/product-search/?term=matcha`.
4. For STAR-K searches, expect company/category listings rather than granular product rows. Use `--section star-k`, `--section star-d`, `--section star-s`, or `--section all` when the symbol section matters.
5. If results include unrelated products, rerun with `--exact` or source-specific filters:
   - OU: `--brand`, `--company`, `--category`
   - OK: `--company`, `--status`, `--symbol`, `--kid`
   - STAR-K: `--company`, `--category`, `--symbol`, `--record-id`
6. Report only records that actually match the user's product or company/category intent. Clearly separate close matches from confirmed matches.
7. Interpret fields conservatively:
   - OU `symbol`: OU mark(s) expected on the product label, such as `OU` or `OU-D`.
   - OU `dpm`: kosher designation, such as Pareve, Dairy, or Meat.
   - OU `status` / `conditions`: certification condition. If it says `Symbol required`, do not say the item is certified unless the actual package bears that symbol.
   - OU `passoverStatus: N`: not certified for Passover.
   - OU `agencyUniqueId`: OU database record ID; include it when disambiguating.
   - OK `symbol`: parsed OK mark, such as `OK`, `OK-D`, `OK-DE`, or `Restriction icon`.
   - OK `status`: designation shown by OK, such as Pareve or Dairy.
   - OK `kid`: OK K-ID record code; include it when disambiguating and link to the K-ID URL when useful.
   - STAR-K `symbols`: listed STAR-K mark(s), such as `STAR-K`, `STAR-D`, or `STAR-S`.
   - STAR-K `categories`: certified category or establishment type shown in the listing.
   - STAR-K `record_id` / `letter_url`: listing code and certification-letter URL; include them when disambiguating.
8. For shopping or sourcing requests, use agency results as certification evidence, then search the web or store/distributor catalogs for purchase availability.

## Script Examples

```bash
# Best first pass for a product name
python3 "$SKILL_DIR/scripts/search_ou_products.py" "Anova burger"

# Remove broad search noise by requiring the exact phrase in product name
python3 "$SKILL_DIR/scripts/search_ou_products.py" "tuna burger" --exact

# Search all pages, then filter locally
python3 "$SKILL_DIR/scripts/search_ou_products.py" "burger" --all-pages --company "Anova Food"

# Emit raw JSON for downstream parsing
python3 "$SKILL_DIR/scripts/search_ou_products.py" "OUV7-70JFBRF" --json

# OK search from a product name or keyword
python3 "$SKILL_DIR/scripts/search_ok_products.py" "matcha"

# OK search from a product-search URL
python3 "$SKILL_DIR/scripts/search_ok_products.py" "https://www.ok.org/product-search/?term=matcha" --limit 25

# OK filtered search
python3 "$SKILL_DIR/scripts/search_ok_products.py" "matcha" --status dairy --symbol OK-D

# OK K-ID lookup after a broad search
python3 "$SKILL_DIR/scripts/search_ok_products.py" "matcha" --kid HCVSGXZ

# STAR-K company/category listing search
python3 "$SKILL_DIR/scripts/search_stark_products.py" "matcha"

# STAR-K filtered search
python3 "$SKILL_DIR/scripts/search_stark_products.py" "pizza" --category "Pizza Shop" --symbol STAR-K

# Search STAR-K, STAR-D, and STAR-S sections
python3 "$SKILL_DIR/scripts/search_stark_products.py" "tea" --section all --limit 25
```

## Response Guidance

When answering users, include:

- Product name, brand/company, certifying agency, and record ID (`agencyUniqueId` for OU, K-ID for OK, STAR-K record ID for STAR-K).
- Symbol, designation/status, Passover status when available, and certification conditions.
- A plain-English conclusion, such as: "This appears in the OU database as OU Pareve, but the package must bear the OU symbol and it is not for Passover."

Avoid treating agency search results as proof for unlabeled packages. OU commonly says `Symbol required`, OK rows may show a restriction icon, and STAR-K often lists companies/categories rather than SKU-level products. In all cases, the actual package label and any agency conditions still matter.
