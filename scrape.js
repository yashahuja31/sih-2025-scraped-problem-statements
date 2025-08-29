
import axios from "axios"             
import * as cheerio from "cheerio"    
import fs from "fs"                  
import path from "path"         

// Base URL listing all problem statements
const LIST_URL = "https://www.sih.gov.in/sih2025PS"   // replace with the actual list page you’re scraping

// Helper to pause between requests, avoids rate limits
const sleep = ms => new Promise(r => setTimeout(r, ms))

async function fetchHTML(url) {
  // Fetch raw HTML text for a given URL
  const res = await axios.get(url, { timeout: 30000 })
  return res.data
}

async function fetchProblemLinks() {
  // Pull the listing page, extract links to each problem
  const html = await fetchHTML(LIST_URL)
  const $ = cheerio.load(html)

  const links = []
  $("a").each((_, el) => {
    const href = $(el).attr("href") || ""
    const text = $(el).text().trim()
    // Filter for problem detail pages, adjust the condition to match real URLs
    if (href.includes("/problem-statement/")) {
      const abs = href.startsWith("http") ? href : new URL(href, LIST_URL).href
      links.push({ url: abs, title: text })
    }
  })

  // De duplicate
  const seen = new Set()
  return links.filter(l => {
    if (seen.has(l.url)) return false
    seen.add(l.url)
    return true
  })
}

function parseProblemPage(html, url) {
  // Parse one problem detail page into a structured object
  const $ = cheerio.load(html)

  // Adjust selectors to the real site structure
  const problemId = $("div:contains('Problem ID')").first().text().match(/Problem ID[:\s]*([\w\-]+)/i)?.[1] || ""
  const title = $("h1,h2").first().text().trim()
  const organization = $("div,span,p").filter((_, el) => $(el).text().includes("Organization")).first().text().replace(/Organization[:\s]*/i, "").trim()
  const category = $("div,span,p").filter((_, el) => $(el).text().includes("Category")).first().text().replace(/Category[:\s]*/i, "").trim()
  const description = $("p,div").filter((_, el) => $(el).text().length > 80).first().text().trim()

  // Example fields, extend as needed by inspecting the DOM
  return {
    url,
    problem_id: problemId,
    title,
    organization,
    category,
    description
  }
}

async function scrapeAll() {
  // Main runner, crawls list, then detail pages, writes JSON
  const outFile = path.join(process.cwd(), "sih_problems.json")
  const links = await fetchProblemLinks()

  const results = []
  for (let i = 0; i < links.length; i++) {
    const { url } = links[i]
    try {
      const html = await fetchHTML(url)
      const item = parseProblemPage(html, url)
      results.push(item)
    } catch (e) {
      // Record failures but continue
      results.push({ url, error: e.message })
    }
    await sleep(400) // be polite
  }

  fs.writeFileSync(outFile, JSON.stringify(results, null, 2), "utf8")
  console.log(`Saved ${results.length} records to ${outFile}`)
}

// Start
scrapeAll().catch(err => {
  console.error("Fatal", err)
  process.exit(1)
})