#!/usr/bin/env node
"use strict";

const fs = require("fs");
const https = require("https");

const API_URL = "https://server.kof-k.org/api/Search/SearchProducts/";
const SEARCH_PAGE_URL = "https://kof-k.org/search-results?type=Product";
const DEFAULT_TIMEOUT_MS = 30000;

function usage() {
  console.log(`Search KOF-K product records.

Usage:
  node search_kofk_products.js <query-or-url> [options]

Options:
  --search-field <product|ukd|manufacturer|brand>  Server field to search. Default: product.
  --limit <n>                                     Maximum rows after local filters. Default: 50. Use 0 for all.
  --exact                                         Require the query phrase in the searched field.
  --manufacturer <text>                           Local filter: manufacturer contains text.
  --brand <text>                                  Local filter: brand contains text.
  --status <text>                                 Filter/status field, such as Parve, Dairy, Meat, or D.E.
  --passover <yes|no>                             Filter Passover status.
  --ukd <text>                                    Local filter: KOF-K UKD contains text.
  --product-code <text>                           Local filter: product code contains text.
  --mode <auto|direct|browser>                    Direct API or browser-assisted search. Default: auto.
  --headless                                      Run browser fallback headless. KOF-K may challenge this.
  --chrome-path <path>                            Chrome/Chromium executable for browser fallback.
  --timeout <seconds>                             Request/browser timeout. Default: 30.
  --json                                          Print parsed rows as JSON.
  --help                                          Show this help.
`);
}

function parseArgs(argv) {
  const args = {
    query: "",
    searchField: "product",
    limit: 50,
    exact: false,
    manufacturer: "",
    brand: "",
    status: "",
    passover: "",
    ukd: "",
    productCode: "",
    mode: "auto",
    headless: false,
    chromePath: process.env.CHROME_PATH || "",
    timeoutMs: DEFAULT_TIMEOUT_MS,
    json: false,
  };

  const positional = [];
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") {
      args.help = true;
    } else if (token === "--exact") {
      args.exact = true;
    } else if (token === "--headless") {
      args.headless = true;
    } else if (token === "--json") {
      args.json = true;
    } else if (token.startsWith("--")) {
      const key = token.slice(2);
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) {
        throw new Error(`${token} requires a value`);
      }
      index += 1;
      switch (key) {
        case "search-field":
          args.searchField = value;
          break;
        case "limit":
          args.limit = parseInteger(value, "--limit");
          break;
        case "manufacturer":
          args.manufacturer = value;
          break;
        case "brand":
          args.brand = value;
          break;
        case "status":
          args.status = value;
          break;
        case "passover":
          args.passover = canonicalPassover(value);
          break;
        case "ukd":
          args.ukd = value;
          break;
        case "product-code":
          args.productCode = value;
          break;
        case "mode":
          args.mode = value;
          break;
        case "chrome-path":
          args.chromePath = value;
          break;
        case "timeout":
          args.timeoutMs = parseFloat(value) * 1000;
          break;
        default:
          throw new Error(`Unknown option: ${token}`);
      }
    } else {
      positional.push(token);
    }
  }

  if (args.help) {
    return args;
  }
  if (positional.length !== 1) {
    throw new Error("Provide exactly one query or KOF-K search URL.");
  }
  if (!["product", "ukd", "manufacturer", "brand"].includes(args.searchField)) {
    throw new Error("--search-field must be product, ukd, manufacturer, or brand.");
  }
  if (!["auto", "direct", "browser"].includes(args.mode)) {
    throw new Error("--mode must be auto, direct, or browser.");
  }
  if (args.limit < 0) {
    throw new Error("--limit must be >= 0.");
  }
  if (!Number.isFinite(args.timeoutMs) || args.timeoutMs <= 0) {
    throw new Error("--timeout must be a positive number.");
  }

  args.query = searchTerm(positional[0]);
  if (!args.query && !args.status && !args.passover) {
    throw new Error("KOF-K product search needs a query, status, or Passover filter.");
  }
  return args;
}

function parseInteger(value, optionName) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) {
    throw new Error(`${optionName} must be an integer.`);
  }
  return parsed;
}

function canonicalPassover(value) {
  const key = value.toLowerCase();
  if (["yes", "y", "true", "1", "passover"].includes(key)) {
    return "Yes";
  }
  if (["no", "n", "false", "0", "not"].includes(key)) {
    return "No";
  }
  throw new Error("--passover must be yes or no.");
}

function searchTerm(value) {
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    return value;
  }
  if (!["kof-k.org", "www.kof-k.org"].includes(parsed.hostname)) {
    throw new Error("KOF-K search URL must be on https://kof-k.org/search-results");
  }
  const params = parsed.searchParams;
  return (
    params.get("ProductName") ||
    params.get("productName") ||
    params.get("product") ||
    params.get("term") ||
    params.get("q") ||
    params.get("search") ||
    params.get("UKD") ||
    params.get("ukd") ||
    ""
  );
}

function payloadFor(args) {
  const payload = {
    UKD: "",
    ProductName: "",
    Manufacturer: "",
    BrandName: "",
    KosherStatus: args.status || "",
    PassoverStatus: args.passover || "",
    Address: "",
    RestaurantName: "",
    SearchTerm: "",
    RestaurantSearchByName: false,
  };
  const fieldMap = {
    product: "ProductName",
    ukd: "UKD",
    manufacturer: "Manufacturer",
    brand: "BrandName",
  };
  payload[fieldMap[args.searchField]] = args.query;
  return payload;
}

function directApiRequest(payload, timeoutMs) {
  const body = JSON.stringify(payload);
  const requestOptions = {
    method: "POST",
    headers: {
      accept: "application/json, text/plain, */*",
      "content-type": "application/json",
      "content-length": Buffer.byteLength(body),
      origin: "https://kof-k.org",
      referer: SEARCH_PAGE_URL,
      "user-agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    },
  };

  return new Promise((resolve, reject) => {
    const request = https.request(API_URL, requestOptions, (response) => {
      const chunks = [];
      response.on("data", (chunk) => chunks.push(chunk));
      response.on("end", () => {
        resolve({
          status: response.statusCode || 0,
          headers: response.headers,
          text: Buffer.concat(chunks).toString("utf8"),
        });
      });
    });
    request.setTimeout(timeoutMs, () => {
      request.destroy(new Error(`KOF-K API request timed out after ${timeoutMs / 1000}s`));
    });
    request.on("error", reject);
    request.write(body);
    request.end();
  });
}

async function browserApiRequest(payload, args) {
  let puppeteer;
  try {
    puppeteer = require("puppeteer");
  } catch (error) {
    throw new Error(
      "KOF-K challenged direct API access and Puppeteer is not available. Install Puppeteer or open https://kof-k.org/search-results?type=Product in a browser."
    );
  }

  const launchOptions = {
    headless: args.headless,
    args: ["--no-sandbox", "--disable-blink-features=AutomationControlled"],
  };
  const executablePath = args.chromePath || defaultChromePath();
  if (executablePath) {
    launchOptions.executablePath = executablePath;
  }

  let browser;
  try {
    browser = await puppeteer.launch(launchOptions);
    const page = await browser.newPage();
    await page.setUserAgent(
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    );
    await page.goto(SEARCH_PAGE_URL, { waitUntil: "networkidle2", timeout: args.timeoutMs });
    return await page.evaluate(
      async ({ apiUrl, requestPayload, timeoutMs }) => {
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), timeoutMs);
        try {
          const response = await fetch(apiUrl, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(requestPayload),
            signal: controller.signal,
          });
          const text = await response.text();
          return {
            status: response.status,
            headers: Object.fromEntries(response.headers.entries()),
            text,
          };
        } finally {
          clearTimeout(id);
        }
      },
      { apiUrl: API_URL, requestPayload: payload, timeoutMs: args.timeoutMs }
    );
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

function defaultChromePath() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || "";
}

function parseRows(response) {
  const text = response.text || "";
  if (isCloudflareChallenge(response)) {
    throw new Error("KOF-K returned a Cloudflare browser challenge for the API request.");
  }
  if (response.status < 200 || response.status >= 300) {
    throw new Error(`KOF-K API returned HTTP ${response.status}: ${text.slice(0, 200)}`);
  }
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch (error) {
    throw new Error(`KOF-K API returned invalid JSON: ${error.message}`);
  }
  if (!Array.isArray(parsed)) {
    throw new Error("KOF-K API returned JSON, but not a product row array.");
  }
  return parsed;
}

function isCloudflareChallenge(response) {
  const headers = response.headers || {};
  const text = response.text || "";
  return (
    headers["cf-mitigated"] === "challenge" ||
    text.includes("Just a moment") ||
    text.includes("__cf_chl") ||
    text.includes("Enable JavaScript and cookies")
  );
}

function norm(value) {
  return String(value || "").toLowerCase();
}

function valueForSearchField(row, searchField) {
  const fieldMap = {
    product: "ProductName",
    ukd: "UKD",
    manufacturer: "Manufacturer",
    brand: "BrandName",
  };
  return row[fieldMap[searchField]] || "";
}

function matchesFilters(row, args) {
  if (args.exact && !norm(valueForSearchField(row, args.searchField)).includes(norm(args.query))) {
    return false;
  }
  if (args.manufacturer && !norm(row.Manufacturer).includes(norm(args.manufacturer))) {
    return false;
  }
  if (args.brand && !norm(row.BrandName).includes(norm(args.brand))) {
    return false;
  }
  if (args.status && !norm(row.KosherStatus).includes(norm(args.status))) {
    return false;
  }
  if (args.passover && norm(row.PassoverStatus) !== norm(args.passover)) {
    return false;
  }
  if (args.ukd && !norm(row.UKD).includes(norm(args.ukd))) {
    return false;
  }
  if (args.productCode && !norm(row.ProductCode).includes(norm(args.productCode))) {
    return false;
  }
  return true;
}

function tooManyResults(rows) {
  return (
    rows.length === 1 &&
    String(rows[0].ProductName || "").trim() === "The search returned too many results. Please refine your search."
  );
}

function printText(rows, total, sourceMode, args) {
  console.log(`Query: ${args.query || "(structured filter only)"}`);
  console.log(`KOF-K request mode: ${sourceMode}`);
  if (tooManyResults(rows)) {
    console.log("KOF-K result: The search returned too many results. Refine the search.");
    return;
  }
  console.log(`KOF-K product matches: ${total}`);
  console.log(`Displayed matches after local filters: ${rows.length}`);
  console.log("");

  rows.forEach((row, index) => {
    console.log(`${index + 1}. ${row.ProductName || ""}`);
    console.log(`   Manufacturer: ${row.Manufacturer || ""}`);
    console.log(`   Brand: ${row.BrandName || ""}`);
    if (row.ProductCode) {
      console.log(`   Product code: ${row.ProductCode}`);
    }
    console.log(`   Status: ${row.KosherStatus || ""}`);
    console.log(`   Passover: ${row.PassoverStatus || ""}`);
    console.log(`   KOF-K UKD: ${row.UKD || ""}`);
    if (row.CertificateLink) {
      console.log(`   Certificate URL: ${row.CertificateLink}`);
    }
    console.log("");
  });
}

async function collectRows(args) {
  const payload = payloadFor(args);
  let directError = null;

  if (args.mode !== "browser") {
    try {
      const response = await directApiRequest(payload, args.timeoutMs);
      return { rows: parseRows(response), mode: "direct" };
    } catch (error) {
      directError = error;
      if (args.mode === "direct") {
        throw error;
      }
    }
  }

  try {
    const response = await browserApiRequest(payload, args);
    return { rows: parseRows(response), mode: "browser" };
  } catch (browserError) {
    if (directError) {
      throw new Error(`${browserError.message} Direct API attempt also failed: ${directError.message}`);
    }
    throw browserError;
  }
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    console.error(error.message);
    console.error("Run with --help for usage.");
    process.exitCode = 2;
    return;
  }

  if (args.help) {
    usage();
    return;
  }

  try {
    const { rows, mode } = await collectRows(args);
    const total = rows.length;
    let filtered = rows.filter((row) => matchesFilters(row, args));
    if (args.limit) {
      filtered = filtered.slice(0, args.limit);
    }

    if (args.json) {
      console.log(
        JSON.stringify(
          {
            query: args.query,
            source_url: SEARCH_PAGE_URL,
            api_url: API_URL,
            mode,
            total,
            results: filtered,
          },
          null,
          2
        )
      );
    } else {
      printText(filtered, total, mode, args);
    }
  } catch (error) {
    console.error(`KOF-K product search failed: ${error.message}`);
    process.exitCode = 2;
  }
}

main();
