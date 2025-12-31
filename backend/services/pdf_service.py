"""
PDF Data Service for NTU Exchange Scraper

Loads and caches PDF vacancy data, provides matching utilities
to enrich database search results with spots and CGPA information.
"""

import re
from pathlib import Path
from typing import Dict, Optional, Tuple
from functools import lru_cache

# Import the existing PDF extractor
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scrapers.pdf_extractor import PDFExtractor


class PDFDataService:
    """
    Service for loading and matching PDF vacancy data.

    Caches PDF data in memory for fast lookups during searches.
    """

    _instance = None
    _pdf_data: Dict = None
    _pdf_df = None

    # Country name aliases for matching
    COUNTRY_ALIASES = {
        'uk': 'united kingdom',
        'united kingdom': 'uk',
        'usa': 'united states',
        'united states': 'usa',
        'united states of america': 'usa',
        'turkiye': 'turkey',
        'turkey': 'turkiye',
        'south korea': 'korea',
        'korea': 'south korea',
        'republic of korea': 'korea',
        'czech republic': 'czechia',
        'czechia': 'czech republic',
        'hong kong sar': 'hong kong',
        'hong kong': 'hong kong sar',
    }

    def __new__(cls):
        """Singleton pattern to cache PDF data."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pdf_data is None:
            self._load_pdf_data()

    def _load_pdf_data(self):
        """Load PDF data from the vacancy list file."""
        # Find the PDF file
        project_root = Path(__file__).parent.parent.parent
        pdf_files = list(project_root.glob("*GEM_Explorer*Vacancy*.pdf"))

        if not pdf_files:
            print("  Warning: No GEM Explorer PDF found. Spots/CGPA data unavailable.")
            self._pdf_data = {}
            return

        pdf_path = pdf_files[0]  # Use the first matching PDF
        print(f"  Loading PDF data from: {pdf_path.name}")

        try:
            extractor = PDFExtractor(str(pdf_path))
            self._pdf_df = extractor.extract_universities_from_pdf()

            # Build lookup dictionaries
            self._pdf_data = {}
            self._name_to_data = {}

            for _, row in self._pdf_df.iterrows():
                uni_name = str(row.get('university_name', '')).strip()
                country = str(row.get('country', '')).strip()

                if not uni_name:
                    continue

                data = {
                    'university_name': uni_name,
                    'country': country,
                    'university_code': row.get('university_code', ''),
                    'sem1_spots': int(row.get('sem1_spots', 0) or 0),
                    'sem2_spots': int(row.get('sem2_spots', 0) or 0),
                    'full_year_spots': int(row.get('full_year_spots', 0) or 0),
                    'min_cgpa': float(row.get('min_cgpa', 0.0) or 0.0),
                    'status_for': row.get('status_for', ''),
                    'remarks': row.get('remarks', '')
                }

                # Store by code
                code = row.get('university_code', '')
                if code:
                    self._pdf_data[code] = data

                # Store by normalized name + country for fuzzy matching
                normalized_key = self._normalize_name(uni_name, country)
                self._name_to_data[normalized_key] = data

            print(f"  ✓ Loaded {len(self._pdf_data)} universities from PDF")

        except Exception as e:
            print(f"  Warning: Failed to load PDF data: {e}")
            self._pdf_data = {}
            self._name_to_data = {}

    def _normalize_name(self, name: str, country: str = "") -> str:
        """Normalize university name for matching."""
        # Convert to lowercase
        normalized = name.lower()

        # Remove common variations
        normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation

        # Remove common suffixes/prefixes that vary
        normalized = normalized.replace('the ', '')
        normalized = normalized.replace(' university', '')
        normalized = normalized.replace('university of ', '')
        normalized = normalized.replace(' of ', ' ')

        # Add country for disambiguation
        if country:
            normalized = f"{country.lower()}_{normalized}"

        return normalized.strip()

    def get_university_data(self, university_name: str, country: str) -> Dict:
        """
        Get PDF data for a university.

        Args:
            university_name: Name of the university
            country: Country name

        Returns:
            Dictionary with sem1_spots, min_cgpa, remarks or defaults if not found
        """
        # Try exact normalized name match
        normalized_key = self._normalize_name(university_name, country)

        if normalized_key in self._name_to_data:
            return self._name_to_data[normalized_key]

        # Try fuzzy matching - find best match
        best_match = self._fuzzy_match(university_name, country)
        if best_match:
            return best_match

        # Return defaults
        return {
            'sem1_spots': 0,
            'min_cgpa': 0.0,
            'remarks': ''
        }

    def _normalize_country(self, country: str) -> set:
        """Get all possible country name variants for matching."""
        country_lower = country.lower()
        variants = {country_lower}
        if country_lower in self.COUNTRY_ALIASES:
            variants.add(self.COUNTRY_ALIASES[country_lower])
        return variants

    def _fuzzy_match(self, university_name: str, country: str) -> Optional[Dict]:
        """
        Try to find a fuzzy match for the university.

        Uses simple substring matching and keyword matching.
        """
        if not self._name_to_data:
            return None

        uni_lower = university_name.lower()
        country_variants = self._normalize_country(country) if country else set()

        # Extract key words from the university name
        keywords = [w for w in uni_lower.split() if len(w) > 3]

        best_score = 0
        best_match = None

        for key, data in self._name_to_data.items():
            # Check country match using aliases
            if country_variants:
                country_match = any(variant in key for variant in country_variants)
                if not country_match:
                    continue

            score = 0
            stored_name = data.get('university_name', '').lower()

            # Check for keyword matches
            for keyword in keywords:
                if keyword in stored_name:
                    score += 1

            # Check for substring match
            if uni_lower in stored_name or stored_name in uni_lower:
                score += 3

            if score > best_score and score >= 2:  # Minimum threshold
                best_score = score
                best_match = data

        return best_match

    def reload(self):
        """Force reload of PDF data."""
        self._pdf_data = None
        self._name_to_data = {}
        self._load_pdf_data()

    def get_stats(self) -> Dict:
        """Get statistics about loaded PDF data."""
        return {
            'loaded': bool(self._pdf_data),
            'university_count': len(self._pdf_data) if self._pdf_data else 0,
            'countries': len(set(d.get('country', '') for d in self._pdf_data.values())) if self._pdf_data else 0
        }


# Global instance for easy access
_pdf_service = None

def get_pdf_service() -> PDFDataService:
    """Get the global PDF service instance."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFDataService()
    return _pdf_service


def enrich_with_pdf_data(university_name: str, country: str) -> Tuple[int, float, str]:
    """
    Convenience function to get spots, CGPA, and remarks for a university.

    Args:
        university_name: Name of the university
        country: Country name

    Returns:
        Tuple of (sem1_spots, min_cgpa, remarks)
    """
    service = get_pdf_service()
    data = service.get_university_data(university_name, country)
    return (
        data.get('sem1_spots', 0),
        data.get('min_cgpa', 0.0),
        data.get('remarks', '')
    )
