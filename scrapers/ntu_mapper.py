"""
NTU Module Mapping Scraper for searching approved course mappings.
"""

import time
import random
from bs4 import BeautifulSoup
from typing import List, Dict
from tqdm import tqdm


class ModuleMappingScraper:
    """Scrape module mappings from NTU INSTEP Past Subject Matching system."""

    def __init__(self, session, search_url: str, rate_limit: Dict):
        """
        Initialize scraper.

        Args:
            session: Authenticated NTUSession instance
            search_url: Module search URL
            rate_limit: Dict with delay_min and delay_max in seconds
        """
        self.session = session
        self.search_url = search_url
        self.delay_min = rate_limit['delay_min']
        self.delay_max = rate_limit['delay_max']
        self.approved_years = ['2024', '2025']

    def search_module_mapping(self, ntu_module: str, university_name: str) -> List[Dict]:
        """
        Search for approved module mappings for a specific NTU module and university.

        Args:
            ntu_module: NTU module code (e.g., 'SC4001')
            university_name: University name to search for

        Returns:
            List of approved mappings
        """
        try:
            # Prepare search parameters
            # These field names may need adjustment based on actual form
            search_params = {
                'p_ntu_code': ntu_module,
                'p_partner_univ': university_name,
                'p_submit': 'Search'
            }

            # Make request
            response = self.session.post(self.search_url, data=search_params)
            response.raise_for_status()

            # Parse results
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find results table
            mappings = []
            table = soup.find('table')  # May need more specific selector

            if table:
                rows = table.find_all('tr')[1:]  # Skip header row

                for row in rows:
                    cols = row.find_all('td')

                    if len(cols) >= 6:  # Adjust based on actual table structure
                        # Extract data from columns
                        # Column indices may need adjustment
                        try:
                            ntu_code = cols[0].text.strip()
                            partner_code = cols[1].text.strip()
                            partner_name = cols[2].text.strip()
                            partner_univ = cols[3].text.strip()
                            status = cols[4].text.strip()
                            year = cols[5].text.strip() if len(cols) > 5 else ''

                            # Filter for approved mappings in 2024/2025
                            if status.lower() == 'approved' and any(y in year for y in self.approved_years):
                                mappings.append({
                                    'ntu_module': ntu_code,
                                    'partner_module_code': partner_code,
                                    'partner_module_name': partner_name,
                                    'university': partner_univ,
                                    'status': status,
                                    'approval_year': year
                                })
                        except (IndexError, AttributeError):
                            continue

            return mappings

        except Exception as e:
            # Log error but don't crash - return empty list
            print(f"\n      Warning: Failed to search {ntu_module} for {university_name}: {e}")
            return []

    def scrape_all_mappings(self, universities: Dict, modules: List[str]) -> Dict:
        """
        Scrape module mappings for all universities and modules.

        Args:
            universities: Dictionary of universities (from PDF extraction)
            modules: List of target module codes

        Returns:
            Dictionary mapping university_id -> module -> list of mappings
        """
        print(f"\n  Searching module mappings for {len(universities)} universities × {len(modules)} modules...")
        print(f"  This will take approximately {len(universities) * len(modules) * 2.5 / 60:.1f} minutes\n")

        mapping_data = {}
        total_searches = len(universities) * len(modules)
        successful_mappings = 0

        # Create progress bar
        with tqdm(total=total_searches, desc="  Searching mappings", unit="search") as pbar:
            for uni_id, uni_info in universities.items():
                uni_name = uni_info['name']
                mapping_data[uni_id] = {}

                for module in modules:
                    # Search for mapping
                    mappings = self.search_module_mapping(module, uni_name)

                    mapping_data[uni_id][module] = mappings

                    if mappings:
                        successful_mappings += 1

                    # Update progress
                    pbar.update(1)
                    pbar.set_postfix({
                        'university': uni_name[:30],
                        'module': module,
                        'found': len(mappings)
                    })

                    # Rate limiting - random delay between min and max
                    delay = random.uniform(self.delay_min, self.delay_max)
                    time.sleep(delay)

        print(f"\n  ✓ Search complete!")
        print(f"    Total searches: {total_searches}")
        print(f"    Found mappings: {successful_mappings} ({successful_mappings/total_searches*100:.1f}%)")

        return mapping_data

    def retry_search(self, ntu_module: str, university_name: str, max_retries: int = 3) -> List[Dict]:
        """
        Search with retry logic for failed requests.

        Args:
            ntu_module: NTU module code
            university_name: University name
            max_retries: Maximum number of retry attempts

        Returns:
            List of mappings
        """
        for attempt in range(max_retries):
            try:
                mappings = self.search_module_mapping(ntu_module, university_name)
                return mappings
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"\n      Retry {attempt + 1}/{max_retries} for {ntu_module} at {university_name} (waiting {wait_time}s)")
                    time.sleep(wait_time)
                else:
                    print(f"\n      Failed after {max_retries} attempts: {ntu_module} at {university_name}")
                    return []
