"""
Mr Bubba Services — Lead List Compilation Service
Fetches lead data from public sources (Clearbit, Hunter.io, public directories)
and compiles targeted lead lists based on client criteria.
"""

import os
import json
import csv
import requests
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

# Configuration
AGENTMAIL_API_KEY = "am_us_inbox_ec1c165f585ed00f28e1a6d17a4ddf198193d215e4c7fa9d8bcc9f6c2b3275e7"
AGENTMAIL_INBOX = "mrbubba@agentmail.to"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

@dataclass
class Lead:
    company_name: str
    website: str
    email: str
    phone: str
    industry: str
    location: str
    company_size: str
    revenue: str
    description: str
    source: str
    confidence: str
    date_found: str

@dataclass
class LeadRequest:
    industry: str
    location: str
    company_size: str
    max_results: int = 50
    keywords: str = ""
    min_revenue: str = ""


class LeadCompiler:
    """Compiles lead lists from multiple public data sources."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 LeadResearchBot/1.0"
        })

    def search_clearbit(self, query: str, limit: int = 10) -> List[Lead]:
        """Search Clearbit Autocomplete API for company data (public endpoint)."""
        leads = []
        try:
            url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={query}"
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for item in data[:limit]:
                    leads.append(Lead(
                        company_name=item.get("name", ""),
                        website=item.get("domain", ""),
                        email="",
                        phone="",
                        industry="",
                        location="",
                        company_size="",
                        revenue="",
                        description=f"Logo: {item.get('logo', 'N/A')}",
                        source="Clearbit",
                        confidence="medium",
                        date_found=datetime.now().isoformat()
                    ))
        except Exception as e:
            print(f"Clearbit search error: {e}")
        return leads

    def search_hunter_io(self, domain: str) -> Dict:
        """Look up email patterns for a domain via Hunter.io (public pattern API)."""
        try:
            url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key=PUBLIC_DEMO"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}

    def search_public_directories(self, industry: str, location: str, limit: int = 20) -> List[Lead]:
        """Search public business directories via web scraping (Yellow Pages, Yelp, etc.)."""
        leads = []
        
        # Search Yelp for business listings
        try:
            search_term = f"{industry} {location}".replace(" ", "+")
            url = f"https://www.yelp.com/search?find_desc={search_term}&start=0"
            resp = self.session.get(url, timeout=15)
            
            if resp.status_code == 200:
                # Extract business names and info from Yelp HTML
                # Pattern for business names in search results
                business_pattern = re.compile(r'"name":"([^"]+)","alternateName"')
                phone_pattern = re.compile(r'"telephone":"([^"]+)"')
                addr_pattern = re.compile(r'"streetAddress":"([^"]+)"')
                zip_pattern = re.compile(r'"postalCode":"([^"]+)"')
                
                names = business_pattern.findall(resp.text)
                phones = phone_pattern.findall(resp.text)
                addresses = addr_pattern.findall(resp.text)
                
                for i, name in enumerate(names[:limit]):
                    lead = Lead(
                        company_name=name.strip(),
                        website="",
                        email="",
                        phone=phones[i] if i < len(phones) else "",
                        industry=industry,
                        location=addresses[i] if i < len(addresses) else location,
                        company_size="",
                        revenue="",
                        description=f"Found on Yelp in {location}",
                        source="Yelp Directory",
                        confidence="medium",
                        date_found=datetime.now().isoformat()
                    )
                    leads.append(lead)
        except Exception as e:
            print(f"Yelp search error: {e}")
        
        return leads

    def search_open_corporates(self, industry: str, location: str, limit: int = 15) -> List[Lead]:
        """Search OpenCorporates API for company registrations."""
        leads = []
        try:
            # Map location to jurisdiction
            jurisdiction_map = {
                "united states": "us", "usa": "us", "us": "us",
                "united kingdom": "gb", "uk": "gb", "gb": "gb",
                "canada": "ca", "ca": "ca"
            }
            jurisdiction = jurisdiction_map.get(location.lower(), "us")
            
            url = f"https://api.opencorporates.com/v0.4/companies/search"
            params = {
                "q": industry,
                "jurisdiction_code": jurisdiction,
                "per_page": limit,
                "page": 1
            }
            resp = self.session.get(url, params=params, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                companies = data.get("results", {}).get("companies", [])
                
                for company_data in companies[:limit]:
                    company = company_data.get("company", {})
                    leads.append(Lead(
                        company_name=company.get("name", ""),
                        website=company.get("registry_url", ""),
                        email=company.get("email_address", ""),
                        phone="",
                        industry=company.get("industry_code", industry),
                        location=f"{company.get('registered_address_in_full', location)}",
                        company_size="",
                        revenue="",
                        description=f"Company Number: {company.get('company_number', 'N/A')}, Status: {company.get('current_status', 'Unknown')}",
                        source="OpenCorporates",
                        confidence="high",
                        date_found=datetime.now().isoformat()
                    ))
        except Exception as e:
            print(f"OpenCorporates search error: {e}")
        
        return leads

    def compile_leads(self, request: LeadRequest) -> List[Lead]:
        """Main compilation method - aggregates leads from all sources."""
        all_leads = []
        
        print(f"\n🔍 Compiling leads for: {request.industry} in {request.location}")
        print(f"   Company size: {request.company_size} | Max results: {request.max_results}")
        print("-" * 60)
        
        # Source 1: Clearbit (company discovery)
        print("  📡 Searching Clearbit company database...")
        query_terms = [request.industry]
        if request.keywords:
            query_terms.append(request.keywords)
        
        for term in query_terms:
            leads = self.search_clearbit(term, limit=10)
            all_leads.extend(leads)
            time.sleep(0.5)  # Rate limiting
        
        print(f"     Found {len(all_leads)} companies from Clearbit")
        
        # Source 2: OpenCorporates (official registrations)
        print("  📡 Searching OpenCorporates registry...")
        oc_leads = self.search_open_corporates(request.industry, request.location)
        all_leads.extend(oc_leads)
        print(f"     Found {len(oc_leads)} companies from OpenCorporates")
        
        # Source 3: Public directories (Yelp, etc.)
        print("  📡 Searching public business directories...")
        dir_leads = self.search_public_directories(request.industry, request.location)
        all_leads.extend(dir_leads)
        print(f"     Found {len(dir_leads)} companies from directories")
        
        # Deduplicate by company name
        seen = set()
        unique_leads = []
        for lead in all_leads:
            name_key = lead.company_name.lower().strip()
            if name_key and name_key not in seen:
                seen.add(name_key)
                unique_leads.append(lead)
        
        # Apply size filter if specified
        if request.company_size:
            size_keywords = {
                "small": ["1-50", "1-10", "11-50", "small", "startup"],
                "medium": ["51-200", "201-500", "medium", "mid"],
                "large": ["501-1000", "1001-5000", "5001+", "enterprise", "large"]
            }
            keywords = size_keywords.get(request.company_size.lower(), [])
            if keywords:
                # In production, we'd filter by actual employee count
                pass
        
        # Limit results
        final_leads = unique_leads[:request.max_results]
        
        print(f"\n✅ Total unique leads compiled: {len(final_leads)}")
        return final_leads

    def generate_csv(self, leads: List[Lead], filename: Optional[str] = None) -> str:
        """Export leads to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lead_list_{timestamp}.csv"
        
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            if leads:
                writer = csv.DictWriter(f, fieldnames=asdict(leads[0]).keys())
                writer.writeheader()
                for lead in leads:
                    writer.writerow(asdict(lead))
        
        print(f"📄 CSV saved to: {filepath}")
        return filepath

    def generate_json(self, leads: List[Lead], filename: Optional[str] = None) -> str:
        """Export leads to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lead_list_{timestamp}.json"
        
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([asdict(lead) for lead in leads], f, indent=2, default=str)
        
        print(f"📄 JSON saved to: {filepath}")
        return filepath


def process_request_from_dict(data: dict) -> LeadRequest:
    """Parse a request dictionary into a LeadRequest object."""
    return LeadRequest(
        industry=data.get("industry", ""),
        location=data.get("location", ""),
        company_size=data.get("company_size", ""),
        max_results=int(data.get("max_results", 50)),
        keywords=data.get("keywords", ""),
        min_revenue=data.get("min_revenue", "")
    )


def main():
    """CLI entry point for lead list compilation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mr Bubba Lead List Compiler")
    parser.add_argument("--industry", required=True, help="Target industry (e.g., 'restaurants', 'SaaS')")
    parser.add_argument("--location", required=True, help="Target location (e.g., 'New York, NY')")
    parser.add_argument("--size", default="", help="Company size (small/medium/large)")
    parser.add_argument("--max-results", type=int, default=50, help="Maximum number of leads (default: 50)")
    parser.add_argument("--keywords", default="", help="Additional keywords to narrow search")
    parser.add_argument("--output-format", choices=["csv", "json", "both"], default="csv")
    
    args = parser.parse_args()
    
    compiler = LeadCompiler()
    request = LeadRequest(
        industry=args.industry,
        location=args.location,
        company_size=args.size,
        max_results=args.max_results,
        keywords=args.keywords
    )
    
    leads = compiler.compile_leads(request)
    
    if leads:
        if args.output_format in ("csv", "both"):
            compiler.generate_csv(leads)
        if args.output_format in ("json", "both"):
            compiler.generate_json(leads)
    else:
        print("⚠️  No leads found. Try broadening your search criteria.")


if __name__ == "__main__":
    main()
