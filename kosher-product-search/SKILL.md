---
name: "kosher-product-search"
description: "Search Orthodox Union (OU), OK Kosher, KOF-K, STAR-K, KLBD / Is It Kosher UK, Kosher Check, OVK, and SKA certification or approved-product listings. Use when the user asks to find, verify, compare, or interpret kosher product records, company listings, certification status, symbols, dairy/pareve/meat designation, Passover status, company/brand listings, K-ID records, KOF-K UKD records, STAR-K record IDs, or whether a product appears in kosher agency databases."
---

# Kosher Product Search

## Quick Start

Use the bundled scripts for repeatable searches:

```bash
SKILL_DIR="$HOME/.codex/skills/kosher-product-search"
python3 "$SKILL_DIR/scripts/search_ou_products.py" "tuna burger" --exact
python3 "$SKILL_DIR/scripts/search_ok_products.py" "matcha" --limit 25
node "$SKILL_DIR/scripts/search_kofk_products.js" "matcha" --limit 25
python3 "$SKILL_DIR/scripts/search_stark_products.py" "pizza" --limit 25
python3 "$SKILL_DIR/scripts/search_klbd_products.py" "matcha" --limit 25
python3 "$SKILL_DIR/scripts/search_koshercheck_products.py" "matcha" --limit 10
python3 "$SKILL_DIR/scripts/search_ovk_products.py" "noodles" --limit 25
python3 "$SKILL_DIR/scripts/search_ska_products.py" "teacakes" --limit 25
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

The KOF-K script calls the public product-search API, using browser fallback when Cloudflare challenges direct CLI access:

```text
POST https://server.kof-k.org/api/Search/SearchProducts/
source page: https://kof-k.org/search-results?type=Product
```

The STAR-K script parses the public listings page:

```text
https://www.star-k.org/listings?section=<star-k|star-d|star-s>&q=<query>
```

The KLBD script calls the Is It Kosher UK JSON query endpoint:

```text
https://isitkosher.uk/api/query?q=<query>&grouped=false
```

The Kosher Check script calls the public WooCommerce product endpoint and, by default, parses each returned product page for detail fields:

```text
https://www.koshercheck.org/wp-json/wc/store/v1/products?search=<query>
```

The OVK script parses the public product table:

```text
https://ovkosher.org/product-search/
```

The SKA script parses the public product-search result table:

```text
https://www.ska.org.uk/product-search?action=search&fb-KosherProduct=<query>
```

The OU, OK, STAR-K, KLBD, Kosher Check, OVK, and SKA scripts use only Python standard library modules. The KOF-K helper uses Node and tries direct API access first; if KOF-K returns a Cloudflare browser challenge, it falls back to Puppeteer/Chrome. If network or browser access is blocked by sandboxing, rerun the same command with the appropriate approval/escalation.

## Workflow

1. Pick the agency source:
   - Use `search_ou_products.py` for OU records.
   - Use `search_ok_products.py` for OK records or when the user links to `ok.org/product-search`.
   - Use `search_kofk_products.js` for KOF-K product rows or when the user links to `kof-k.org/search-results?type=Product`.
   - Use `search_stark_products.py` for STAR-K company/category listings or when the user links to `star-k.org/listings`.
   - Use `search_klbd_products.py` for KLBD / Is It Kosher UK records, especially products bought/manufactured for the UK market.
   - Use `search_koshercheck_products.py` for Kosher Check product records.
   - Use `search_ovk_products.py` for OVK consumer product table records.
   - Use `search_ska_products.py` for Sephardi Kashrut Authority Certified/Approved product records.
2. Search broadly with the product name, UPC, brand, or company. OU agency IDs, KOF-K UKD values, and STAR-K record IDs can be searched directly. OK K-IDs are only available after the public OK product-search page returns a matching product/company row; search by product or company first, then filter with `--kid`.
3. For OK searches, pass either a search term or the full OK search URL, such as `https://www.ok.org/product-search/?term=matcha`.
4. For KOF-K searches, expect product-level rows with UKD and certificate links. Use `--search-field ukd`, `--search-field manufacturer`, or `--search-field brand` when the query is not a product name.
5. For STAR-K searches, expect company/category listings rather than granular product rows. Use `--section star-k`, `--section star-d`, `--section star-s`, or `--section all` when the symbol section matters.
6. If results include unrelated products, rerun with `--exact` or source-specific filters:
   - OU: `--brand`, `--company`, `--category`, `--record-id`
   - OK: `--company`, `--status`, `--symbol`, `--kid`
   - KOF-K: `--manufacturer`, `--brand`, `--status`, `--passover`, `--ukd`, `--product-code`
   - STAR-K: `--company`, `--category`, `--symbol`, `--record-id`
   - KLBD: `--brand`, `--category`, `--status`, `--designation`, `--certification`
   - Kosher Check: `--brand`, `--company`, `--category`, `--designation`, `--record-id`
   - OVK: `--brand`, `--status`, `--passover`, `--restriction`
   - SKA: `--field product|brand|category`, `--brand`, `--category`, `--status`, `--designation`, `--logo`, `--passover`
7. Report only records that actually match the user's product or company/category intent. Clearly separate close matches from confirmed matches.
8. Interpret fields conservatively:
   - OU `symbol`: OU mark(s) expected on the product label, such as `OU` or `OU-D`.
   - OU `dpm`: kosher designation, such as Pareve, Dairy, or Meat.
   - OU `status` / `conditions`: certification condition. If it says `Symbol required`, do not say the item is certified unless the actual package bears that symbol.
   - OU `passoverStatus: N`: not certified for Passover.
   - OU `agencyUniqueId`: OU database record ID; include it when disambiguating.
   - OK `symbol`: parsed OK mark, such as `OK`, `OK-D`, `OK-DE`, or `Restriction icon`.
   - OK `status`: designation shown by OK, such as Pareve or Dairy.
   - OK `kid`: OK K-ID record code; include it when disambiguating and link to the K-ID URL when useful.
   - KOF-K `KosherStatus`: designation shown by KOF-K, such as Parve, Dairy, Meat, or D.E.
   - KOF-K `PassoverStatus`: whether KOF-K marks the product as Passover certified (`Yes`) or not (`No`).
   - KOF-K `UKD` / `CertificateLink`: KOF-K product record code and certificate URL; include them when disambiguating.
   - STAR-K `symbols`: listed STAR-K mark(s), such as `STAR-K`, `STAR-D`, or `STAR-S`.
   - STAR-K `categories`: certified category or establishment type shown in the listing.
   - STAR-K `record_id` / `letter_url`: listing code and certification-letter URL; include them when disambiguating.
   - KLBD results apply to products manufactured for the UK market. Treat `kosher_raw_data`, `certification`, `milkmeat`, and notes as the controlling evidence.
   - Kosher Check `symbol_condition` commonly says a kosher symbol is required; do not treat an unlabeled package as certified.
   - OVK's public table says it only includes some popular consumer certified items; absence from this table is not complete evidence.
   - SKA distinguishes `Certified` from `Approved`; include `SKA Logo`, `Passover`, and `Notes` fields when present.
9. For shopping or sourcing requests, use agency results as certification evidence, then search the web or store/distributor catalogs for purchase availability.

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

# Filter broad OU results by record ID
python3 "$SKILL_DIR/scripts/search_ou_products.py" "matcha" --all-pages --record-id OUV7-FIHGTOC

# OK search from a product name or keyword
python3 "$SKILL_DIR/scripts/search_ok_products.py" "matcha"

# OK search from a product-search URL
python3 "$SKILL_DIR/scripts/search_ok_products.py" "https://www.ok.org/product-search/?term=matcha" --limit 25

# OK filtered search
python3 "$SKILL_DIR/scripts/search_ok_products.py" "matcha" --status dairy --symbol OK-D

# OK K-ID lookup after a broad search
python3 "$SKILL_DIR/scripts/search_ok_products.py" "matcha" --kid HCVSGXZ

# KOF-K product search
node "$SKILL_DIR/scripts/search_kofk_products.js" "matcha" --limit 25

# KOF-K filtered search
node "$SKILL_DIR/scripts/search_kofk_products.js" "coffee" --status Parve --passover no --limit 10

# KOF-K UKD lookup
node "$SKILL_DIR/scripts/search_kofk_products.js" "KF7JNHKQLLP" --search-field ukd

# STAR-K company/category listing search
python3 "$SKILL_DIR/scripts/search_stark_products.py" "matcha"

# STAR-K filtered search
python3 "$SKILL_DIR/scripts/search_stark_products.py" "pizza" --category "Pizza Shop" --symbol STAR-K

# Search STAR-K, STAR-D, and STAR-S sections
python3 "$SKILL_DIR/scripts/search_stark_products.py" "tea" --section all --limit 25

# Direct STAR-K record ID lookup
python3 "$SKILL_DIR/scripts/search_stark_products.py" "P4XL0PQQ"

# KLBD / Is It Kosher UK search
python3 "$SKILL_DIR/scripts/search_klbd_products.py" "matcha" --limit 25

# KLBD filtered search
python3 "$SKILL_DIR/scripts/search_klbd_products.py" "matcha" --certification klbd --designation parev

# Kosher Check search with product-page details
python3 "$SKILL_DIR/scripts/search_koshercheck_products.py" "matcha" --limit 10

# Kosher Check faster search using only the product API
python3 "$SKILL_DIR/scripts/search_koshercheck_products.py" "matcha" --no-details --limit 25

# OVK table search
python3 "$SKILL_DIR/scripts/search_ovk_products.py" "noodles" --status pareve

# SKA product search
python3 "$SKILL_DIR/scripts/search_ska_products.py" "teacakes" --limit 25

# SKA brand search
python3 "$SKILL_DIR/scripts/search_ska_products.py" "ocado" --field brand --status Certified
```

## Response Guidance

When answering users, include:

- Product name, brand/company, certifying agency, and record ID when available (`agencyUniqueId` for OU, K-ID for OK, UKD for KOF-K, STAR-K record ID for STAR-K, Kosher Check SKU/record).
- Symbol, designation/status, Passover status when available, and certification conditions.
- A plain-English conclusion, such as: "This appears in the OU database as OU Pareve, but the package must bear the OU symbol and it is not for Passover."

Avoid treating agency search results as proof for unlabeled packages. OU commonly says `Symbol required`, OK rows may show a restriction icon, KOF-K product rows may describe ingredients or industrial products rather than retail SKUs, and STAR-K often lists companies/categories rather than SKU-level products. In all cases, the actual package label and any agency conditions still matter.
