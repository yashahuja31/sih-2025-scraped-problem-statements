**Smart India Hackathon Problem Statements 2025 Scraper**

A Node.js scraper that collects Smart India Hackathon problem statements and saves structured JSON plus helper artifacts.

##Features

Fetches problem statements list and details
Outputs clean JSON, PDF link list, and a CSV if needed
Retries, polite delays, and simple error logging
Project Structure

package.json, package-lock.json, node_modules, .gitignore
scrape.js, main Node script, runs the scraper end to end
scrape.pyw, optional helper, lightweight post processing or CSV generation
sih_problems.json, consolidated problems data, title, org, category, difficulty, description, links
sih_2025_data_problems.json, year specific dump of problems in JSON
sih_2025_data_pdf_links.json, extracted PDF or attachment links per problem
README.md, this file
Prerequisites

Node 18 or newer
npm 9 or newer
Python 3 if you want to run scrape.pyw
Internet access to SIH site
Install

# install dependencies
npm install
Usage

# run the scraper
node scrape.js

# optional, run the Python helper for CSV
python scrape.pyw
Configuration

Edit constants inside scrape.js
BASE_URL, year route or endpoint
OUTPUT_DIR, default is project root
CONCURRENCY, number of parallel requests
REQUEST_DELAY_MS, polite delay between calls
For Python helper, adjust input and output file paths at the top of scrape.pyw
Outputs

sih_problems.json, unified JSON for all years scraped
sih_2025_data_problems.json, year specific JSON
sih_2025_data_pdf_links.json, list of downloadable resources
Data Fields

id, unique problem id if available
title, organization, category, domain
difficulty, student category, track, year
description, expected solution, constraints
links, array of URLs, PDF or reference
meta, timestamps, source URL, fetch status
Common Gotchas

404 from site, the route changed, update BASE_URL to the current year path
0 records, the page renders via JS, switch to the JSON API endpoint or use a headless browser
Blocked by server, increase REQUEST_DELAY_MS, lower CONCURRENCY, set a real User Agent header
HTML changes, update selectors in scrape.js accordingly
Scripts in package.json

start, node scrape.js
format or lint if you add them
Extending

Add CLI args with yargs for year and output
Add Puppeteer for dynamic routes
Add dedupe by id and merge by year
License

MIT, feel free to use and modify
Credits


Built by you, data belongs to Smart India Hackathon organizers and respective sources
