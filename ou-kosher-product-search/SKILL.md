---
name: ou-kosher-product-search
description: Search Orthodox Union (OU) kosher product certification listings through the OU product search API. Use when the user asks to find, verify, compare, or interpret OU kosher product records, certification status, symbols, dairy/pareve/meat designation, Passover status, company/brand listings, or asks whether a product appears in the OU kosher database.
---

# OU Kosher Product Search

## Quick Start

Use the bundled script for repeatable searches:

```bash
python3 "$HOME/.claude/skills/ou-kosher-product-search/scripts/search_ou_products.py" "tuna burger" --exact
```

The script calls:

```text
https://productsearch-v2.oukosher.org/api/v1/product?page=1&limit=50&query=<query>
```

It uses only Python standard library modules.

## Workflow

1. Search broadly with the product name, UPC, brand, company, or OU agency ID.
2. If results include unrelated products, rerun with `--exact` or filters such as `--brand`, `--company`, or `--category`.
3. Report only records that actually match the user's product. Clearly separate close matches from confirmed matches.
4. Interpret OU fields conservatively:
   - `symbol`: OU mark(s) expected on the product label, such as `OU` or `OU-D`.
   - `dpm`: kosher designation, such as Pareve, Dairy, Meat, or Dairy Equipment.
   - `status` / `conditions`: certification condition. If it says `Symbol required`, do not say the item is certified unless the actual package bears that symbol.
   - `passoverStatus: N`: not certified for Passover.
   - `agencyUniqueId`: OU database record ID; include it when disambiguating.
5. For shopping, nutrition, or recommendation requests, use OU results as certification evidence, then search current product pages or store catalogs for purchase availability, ingredients, nutrition facts, and current packaging.

## Script Examples

```bash
# Best first pass for a product name
python3 "$HOME/.claude/skills/ou-kosher-product-search/scripts/search_ou_products.py" "Anova burger"

# Remove broad search noise by requiring the exact phrase in product name
python3 "$HOME/.claude/skills/ou-kosher-product-search/scripts/search_ou_products.py" "tuna burger" --exact

# Search all pages, then filter locally
python3 "$HOME/.claude/skills/ou-kosher-product-search/scripts/search_ou_products.py" "burger" --all-pages --company "Anova Food"

# Emit raw JSON for downstream parsing
python3 "$HOME/.claude/skills/ou-kosher-product-search/scripts/search_ou_products.py" "OUV7-70JFBRF" --json
```

## Response Guidance

When answering users, include:

- Product name, brand, company, and OU record ID.
- Symbol, DPM designation, Passover status, and status/conditions.
- A plain-English conclusion, such as: "This appears in the OU database as OU Pareve, but the package must bear the OU symbol and it is not for Passover."

Avoid treating OU search results as proof for unlabeled packages. The OU database commonly says `Symbol required`; that means the package label still matters.
