"""
Recommendation Engine for NTU Exchange University Scraper API.
Orchestrates the university recommendation pipeline with caching.

This service wraps existing CLI scrapers and processors without modification,
adding a caching layer for improved performance.
"""

import os
import sys
import yaml
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Add parent directory to path to import existing modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scrapers.pdf_extractor import PDFExtractor
from scrapers.selenium_scraper import SeleniumNTUScraper
from processors.data_cleaner import clean_and_group_universities, normalize_mappings
from processors.matcher import combine_data_sources
from processors.ranker import filter_and_rank
from backend.services.cache_manager import CacheManager


class RecommendationEngine:
    """
    Service that orchestrates the university recommendation pipeline.

    Integrates:
    - PDF extraction (scrapers/pdf_extractor.py)
    - Selenium-based module mapping scraping (scrapers/selenium_scraper.py)
    - Data cleaning and matching (processors/)
    - Intelligent caching (cache_manager.py)
    """

    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Initialize recommendation engine.

        Args:
            config_path: Path to configuration YAML file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.cache_manager = CacheManager()

    def _load_config(self) -> dict:
        """
        Load configuration from YAML file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def search_universities(
        self,
        credentials: Tuple[str, str, str],
        target_countries: Optional[List[str]] = None,
        target_modules: Optional[List[str]] = None,
        min_mappable_modules: int = 2,
        use_cache: bool = True,
        headless: bool = True
    ) -> Tuple[List[Tuple[str, Dict]], bool, Optional[str]]:
        """
        Execute university search with caching.

        This is the main entry point for the API. It orchestrates the entire
        pipeline: PDF extraction → Selenium scraping → Processing → Ranking.

        Args:
            credentials: Tuple of (username, password, domain)
            target_countries: List of countries to filter (None = use config)
            target_modules: List of module codes (None = use config)
            min_mappable_modules: Minimum mappable modules threshold
            use_cache: Whether to use cached data
            headless: Run Selenium in headless mode

        Returns:
            Tuple of (ranked_results, cache_used, cache_timestamp)
            - ranked_results: List of (university_id, university_data) tuples
            - cache_used: Boolean indicating if cache was used
            - cache_timestamp: ISO timestamp of cached data (or None)

        Raises:
            FileNotFoundError: If PDF file not found
            RuntimeError: If browser startup or login fails
        """
        username = credentials[0]

        # Use config defaults if not provided
        countries = target_countries or self.config['target_countries']
        modules = target_modules or self.config['target_modules']

        # Update config with request parameters
        search_config = self.config.copy()
        search_config['target_countries'] = countries
        search_config['target_modules'] = modules
        search_config['min_mappable_modules'] = min_mappable_modules

        # Step 1: Get university list (with caching)
        print(f"\n[Step 1/3] Getting university list...")
        universities, uni_cache_used, uni_cache_time = self._get_universities(
            search_config, use_cache
        )
        print(f"  {'✓ Loaded from cache' if uni_cache_used else '✓ Extracted from PDF'}")

        # Step 2: Get module mappings (with caching)
        print(f"\n[Step 2/3] Getting module mappings...")
        mapping_data, map_cache_used, map_cache_time = self._get_mappings(
            credentials, universities, modules, countries,
            username, use_cache, headless
        )
        print(f"  {'✓ Loaded from cache' if map_cache_used else '✓ Scraped from NTU'}")

        # Step 3: Process and rank (no caching - fast operation)
        print(f"\n[Step 3/3] Processing and ranking...")
        ranked_results = self._process_and_rank(
            universities, mapping_data, search_config
        )
        print(f"  ✓ Ranked {len(ranked_results)} universities")

        # Determine overall cache status
        cache_used = uni_cache_used and map_cache_used
        cache_timestamp = map_cache_time if cache_used else None

        return ranked_results, cache_used, cache_timestamp

    def _get_universities(
        self,
        config: dict,
        use_cache: bool
    ) -> Tuple[dict, bool, Optional[str]]:
        """
        Get university list from PDF with caching.

        Args:
            config: Configuration dictionary with target_countries, student_college
            use_cache: Whether to attempt to use cache

        Returns:
            Tuple of (universities, cache_used, cache_timestamp)

        Raises:
            FileNotFoundError: If PDF file doesn't exist
        """
        # Try cache first
        if use_cache:
            cached = self.cache_manager.get_universities(config)
            if cached:
                universities, cache_time = cached
                return universities, True, cache_time

        # Cache miss - extract from PDF
        pdf_path = config['pdf_file']

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(
                f"PDF file not found: {pdf_path}\n"
                f"Please ensure the GEM Explorer PDF is in the project directory."
            )

        # Extract from PDF (using existing scraper)
        extractor = PDFExtractor(pdf_path)
        df = extractor.extract_universities_from_pdf()
        universities = extractor.filter_target_universities(df, config)

        # Save to cache for next time
        if use_cache:
            self.cache_manager.save_universities(universities, config)

        return universities, False, None

    def _get_mappings(
        self,
        credentials: Tuple[str, str, str],
        universities: dict,
        modules: list,
        countries: list,
        username: str,
        use_cache: bool,
        headless: bool
    ) -> Tuple[dict, bool, Optional[str]]:
        """
        Get module mappings with caching.

        Args:
            credentials: Tuple of (username, password, domain)
            universities: Dictionary of universities to search
            modules: List of module codes
            countries: List of countries
            username: NTU username (for cache key)
            use_cache: Whether to attempt to use cache
            headless: Run browser in headless mode

        Returns:
            Tuple of (mapping_data, cache_used, cache_timestamp)

        Raises:
            RuntimeError: If browser startup or login fails
        """
        # Try cache first
        if use_cache:
            cached = self.cache_manager.get_mappings(countries, modules, username)
            if cached:
                mapping_data, cache_time = cached
                return mapping_data, True, cache_time

        # Cache miss - scrape using Selenium (using existing scraper)
        print("  Starting Selenium browser...")
        scraper = SeleniumNTUScraper(credentials, self.config, headless=headless)

        try:
            # Start browser
            if not scraper.start():
                raise RuntimeError("Failed to start Chrome browser")

            # Login to NTU SSO
            print("  Logging in to NTU SSO...")
            if not scraper.login():
                raise RuntimeError(
                    "Login failed - please check your credentials.\n"
                    "Ensure username, password, and domain are correct."
                )

            # Scrape all mappings
            print(f"  Scraping mappings for {len(universities)} universities...")
            print(f"  (This will take approximately {len(universities) * 2.5 / 60:.1f} minutes)")
            mapping_data = scraper.scrape_all_mappings(universities, modules)

            # Save to cache for next time
            if use_cache:
                print("  Saving to cache...")
                self.cache_manager.save_mappings(
                    mapping_data, countries, modules, username
                )

            return mapping_data, False, None

        finally:
            # Always close browser
            scraper.close()

    def _process_and_rank(
        self,
        universities: dict,
        mapping_data: dict,
        config: dict
    ) -> List[Tuple[str, Dict]]:
        """
        Process, clean, match, and rank university data.

        Uses existing processors without modification.

        Args:
            universities: University data from PDF
            mapping_data: Module mapping data from scraper
            config: Configuration dictionary

        Returns:
            List of (university_id, university_data) tuples, ranked
        """
        # Clean and group universities (handles campus variations)
        cleaned_unis = clean_and_group_universities(universities)

        # Normalize mapping data (standardizes module names, etc.)
        normalized_mappings = normalize_mappings(mapping_data)

        # Combine data sources (match universities with their mappings)
        integrated_data = combine_data_sources(cleaned_unis, normalized_mappings)

        # Filter and rank (by country → mappable modules → spots → CGPA)
        min_mappable = config.get('min_mappable_modules', 2)
        ranked_data = filter_and_rank(integrated_data, min_mappable=min_mappable)

        return ranked_data
