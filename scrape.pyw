import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import csv
from urllib.parse import urljoin, urlparse
import logging
from typing import List, Dict, Optional
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SIHScraper:
    def __init__(self, base_url: str = "https://sih.gov.in/sih2025PS", delay: float = 1.0):
        """
        Initialize the SIH scraper
        
        Args:
            base_url: Base URL for SIH problem statements
            delay: Delay between requests to be respectful to the server
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        
        # Setup headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.problem_statements = []
        
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Get page content with error handling
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Add delay to be respectful
            time.sleep(self.delay)
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_problem_statement_details(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract problem statement details from the main page
        
        Args:
            soup: BeautifulSoup object of the main page
            
        Returns:
            List of problem statement dictionaries
        """
        problem_statements = []
        
        # Method 1: Look for table structures (common in government websites)
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            headers = []
            
            # Extract headers
            header_row = rows[0] if rows else None
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Extract data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= len(headers):
                    problem_data = {}
                    for i, cell in enumerate(cells):
                        header = headers[i] if i < len(headers) else f"column_{i}"
                        problem_data[header] = cell.get_text(strip=True)
                        
                        # Extract links if present
                        links = cell.find_all('a')
                        if links:
                            problem_data[f"{header}_links"] = [
                                urljoin(self.base_url, link.get('href', '')) 
                                for link in links if link.get('href')
                            ]
                    
                    if problem_data:
                        problem_statements.append(problem_data)
        
        # Method 2: Look for card-based layouts
        cards = soup.find_all(['div'], class_=lambda x: x and any(
            term in x.lower() for term in ['card', 'problem', 'statement', 'item', 'entry']
        ))
        
        for card in cards:
            problem_data = {}
            
            # Extract title
            title_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if title_elem:
                problem_data['title'] = title_elem.get_text(strip=True)
            
            # Extract organization
            org_elem = card.find(text=re.compile(r'organization|ministry|department', re.I))
            if org_elem:
                problem_data['organization'] = org_elem.parent.get_text(strip=True)
            
            # Extract category
            cat_elem = card.find(text=re.compile(r'category|software|hardware', re.I))
            if cat_elem:
                problem_data['category'] = cat_elem.parent.get_text(strip=True)
            
            # Extract all text content
            problem_data['full_content'] = card.get_text(strip=True)
            
            # Extract links
            links = card.find_all('a')
            if links:
                problem_data['links'] = [
                    urljoin(self.base_url, link.get('href', '')) 
                    for link in links if link.get('href')
                ]
            
            if problem_data:
                problem_statements.append(problem_data)
        
        # Method 3: Look for list-based structures
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = list_elem.find_all('li')
            for item in items:
                problem_data = {
                    'content': item.get_text(strip=True),
                    'html_content': str(item)
                }
                
                # Extract links
                links = item.find_all('a')
                if links:
                    problem_data['links'] = [
                        urljoin(self.base_url, link.get('href', '')) 
                        for link in links if link.get('href')
                    ]
                
                problem_statements.append(problem_data)
        
        return problem_statements
    
    def extract_pdf_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract PDF download links from the page
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of PDF URLs
        """
        pdf_links = []
        
        # Find all links pointing to PDFs
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if href.lower().endswith('.pdf') or 'pdf' in href.lower():
                full_url = urljoin(self.base_url, href)
                pdf_links.append(full_url)
        
        return pdf_links
    
    def scrape_main_page(self) -> Dict:
        """
        Scrape the main SIH problem statements page
        
        Returns:
            Dictionary containing all scraped data
        """
        soup = self.get_page_content(self.base_url)
        if not soup:
            logger.error("Failed to fetch main page")
            return {}
        
        # Extract basic page info
        page_info = {
            'title': soup.find('title').get_text(strip=True) if soup.find('title') else 'N/A',
            'url': self.base_url,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Extract problem statements
        problem_statements = self.extract_problem_statement_details(soup)
        
        # Extract PDF links
        pdf_links = self.extract_pdf_links(soup)
        
        # Extract statistics if available
        stats = {}
        stat_elements = soup.find_all(text=re.compile(r'\d+.*(?:problem|statement|total)', re.I))
        for stat in stat_elements:
            stats[stat.strip()] = stat.parent.get_text(strip=True) if stat.parent else stat.strip()
        
        # Find navigation or pagination links
        nav_links = []
        nav_elements = soup.find_all(['nav', 'div'], class_=lambda x: x and 'nav' in x.lower())
        for nav in nav_elements:
            links = nav.find_all('a', href=True)
            nav_links.extend([urljoin(self.base_url, link.get('href')) for link in links])
        
        return {
            'page_info': page_info,
            'problem_statements': problem_statements,
            'pdf_links': pdf_links,
            'statistics': stats,
            'navigation_links': nav_links,
            'total_problems_found': len(problem_statements)
        }
    
    def scrape_detailed_pages(self, problem_links: List[str]) -> List[Dict]:
        """
        Scrape detailed problem statement pages
        
        Args:
            problem_links: List of URLs to detailed problem pages
            
        Returns:
            List of detailed problem data
        """
        detailed_problems = []
        
        for link in problem_links:
            soup = self.get_page_content(link)
            if not soup:
                continue
            
            problem_detail = {
                'url': link,
                'title': soup.find('title').get_text(strip=True) if soup.find('title') else 'N/A',
                'content': soup.get_text(strip=True),
                'html_content': str(soup),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Extract specific fields if they exist
            fields_to_extract = [
                'problem statement', 'description', 'expected solution',
                'organization', 'ministry', 'category', 'domain',
                'technology bucket', 'dataset', 'deadline'
            ]
            
            for field in fields_to_extract:
                field_elem = soup.find(text=re.compile(field, re.I))
                if field_elem and field_elem.parent:
                    problem_detail[field.replace(' ', '_')] = field_elem.parent.get_text(strip=True)
            
            detailed_problems.append(problem_detail)
        
        return detailed_problems
    
    def save_to_files(self, data: Dict, filename_prefix: str = "sih_2025_data"):
        """
        Save scraped data to multiple formats
        
        Args:
            data: Dictionary containing scraped data
            filename_prefix: Prefix for output files
        """
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # Save to JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {json_filename}")
        
        # Save problem statements to CSV if available
        if data.get('problem_statements'):
            csv_filename = f"{filename_prefix}_problems_{timestamp}.csv"
            df = pd.DataFrame(data['problem_statements'])
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            logger.info(f"Problem statements saved to {csv_filename}")
        
        # Save PDF links if available
        if data.get('pdf_links'):
            pdf_links_file = f"{filename_prefix}_pdf_links_{timestamp}.txt"
            with open(pdf_links_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(data['pdf_links']))
            logger.info(f"PDF links saved to {pdf_links_file}")
    
    def run_full_scrape(self, save_files: bool = True) -> Dict:
        """
        Run complete scraping process
        
        Args:
            save_files: Whether to save data to files
            
        Returns:
            Dictionary containing all scraped data
        """
        logger.info("Starting SIH 2025 Problem Statements scraping...")
        
        # Scrape main page
        main_data = self.scrape_main_page()
        
        if not main_data:
            logger.error("No data found on main page")
            return {}
        
        # Extract links for detailed scraping
        detailed_links = []
        for problem in main_data.get('problem_statements', []):
            if 'links' in problem:
                detailed_links.extend(problem['links'])
        
        # Add navigation links
        detailed_links.extend(main_data.get('navigation_links', []))
        
        # Remove duplicates
        detailed_links = list(set(detailed_links))
        
        logger.info(f"Found {len(detailed_links)} links for detailed scraping")
        
        # Scrape detailed pages (limit to avoid overwhelming)
        if detailed_links:
            detailed_data = self.scrape_detailed_pages(detailed_links[:50])  # Limit to first 50
            main_data['detailed_problems'] = detailed_data
        
        # Save data if requested
        if save_files:
            self.save_to_files(main_data)
        
        logger.info(f"Scraping completed! Found {main_data.get('total_problems_found', 0)} problem statements")
        
        return main_data

def main():
    """
    Main function to run the scraper
    """
    # Initialize scraper
    scraper = SIHScraper(
        base_url="https://sih.gov.in/sih2025PS",
        delay=1.5  # Be respectful with requests
    )
    
    try:
        # Run full scrape
        data = scraper.run_full_scrape(save_files=True)
        
        # Print summary
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        print(f"Total problem statements found: {data.get('total_problems_found', 0)}")
        print(f"PDF links found: {len(data.get('pdf_links', []))}")
        print(f"Navigation links found: {len(data.get('navigation_links', []))}")
        print(f"Detailed pages scraped: {len(data.get('detailed_problems', []))}")
        
        # Show sample data
        if data.get('problem_statements'):
            print("\nSample problem statement:")
            sample = data['problem_statements'][0]
            for key, value in sample.items():
                if isinstance(value, str) and len(value) < 100:
                    print(f"  {key}: {value}")
        
        return data
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return None

if __name__ == "__main__":
    # Run the scraper
    scraped_data = main()
    
    # Optional: Download PDFs (uncomment if needed)
    """
    if scraped_data and scraped_data.get('pdf_links'):
        print("\nDo you want to download PDF files? (y/n): ", end='')
        if input().lower().startswith('y'):
            for i, pdf_url in enumerate(scraped_data['pdf_links'][:10]):  # Limit to 10 PDFs
                try:
                    response = requests.get(pdf_url, timeout=30)
                    if response.status_code == 200:
                        filename = f"sih_2025_pdf_{i+1}.pdf"
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        print(f"Downloaded: {filename}")
                        time.sleep(2)  # Delay between downloads
                except Exception as e:
                    print(f"Failed to download {pdf_url}: {e}")
    """