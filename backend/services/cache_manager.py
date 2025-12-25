"""
Cache Manager for NTU Exchange Scraper API.
Implements JSON file-based caching with TTL support.

Cache Strategy:
- University list (PDF): 365 days TTL (changes yearly)
- Module mappings: 30 days TTL (can change periodically)
- Cache key for mappings: hash(countries + modules + username)
"""

import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from pathlib import Path


class CacheManager:
    """
    Manages JSON file-based caching with TTL support.

    Uses hash-based cache keys to support multiple search configurations.
    Separate TTLs for university data (yearly) vs module mappings (monthly).
    """

    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.universities_cache = self.cache_dir / "universities.json"
        self.mappings_cache_dir = self.cache_dir / "mappings"

        # TTL in days
        self.UNIVERSITIES_TTL = 365  # 1 year - PDF changes yearly
        self.MAPPINGS_TTL = 30       # 30 days - mappings can change

        # Ensure cache directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.mappings_cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_mapping_cache_key(self,
                                     countries: List[str],
                                     modules: List[str],
                                     username: str) -> str:
        """
        Generate cache key for mapping data.

        Key includes countries, modules, and username because:
        - Different users may have different permissions/results
        - Different search parameters need separate caches

        Args:
            countries: List of country names
            modules: List of module codes
            username: NTU username

        Returns:
            SHA256 hash of the sorted parameters
        """
        # Sort to ensure consistent key regardless of input order
        sorted_countries = sorted(countries)
        sorted_modules = sorted(modules)

        # Create hash key
        key_string = f"{sorted_countries}_{sorted_modules}_{username}"
        hash_key = hashlib.sha256(key_string.encode()).hexdigest()
        return hash_key

    def _is_cache_valid(self, cache_file: Path, ttl_days: int) -> bool:
        """
        Check if cache file exists and is within TTL.

        Args:
            cache_file: Path to cache file
            ttl_days: Time-to-live in days

        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_file.exists():
            return False

        # Read cache metadata
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            # Parse cached timestamp
            cached_at_str = cache_data.get('cached_at')
            if not cached_at_str:
                return False

            cached_at = datetime.fromisoformat(cached_at_str)
            expiry = cached_at + timedelta(days=ttl_days)

            # Check if expired
            return datetime.now() < expiry
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache file
            return False

    def get_universities(self, config: dict) -> Optional[Tuple[dict, str]]:
        """
        Get cached university list from PDF.

        Cache is invalidated if config changes (different countries or college).

        Args:
            config: Configuration dictionary with target_countries and student_college

        Returns:
            Tuple of (universities_dict, cache_timestamp) if valid cache exists,
            None otherwise
        """
        if not self._is_cache_valid(self.universities_cache, self.UNIVERSITIES_TTL):
            return None

        try:
            with open(self.universities_cache, 'r') as f:
                cache_data = json.load(f)

            # Verify config matches (countries, student_college)
            # If config changed, cache is invalid
            cached_config = cache_data.get('config', {})
            if (cached_config.get('target_countries') != config.get('target_countries') or
                cached_config.get('student_college') != config.get('student_college')):
                return None  # Config changed, invalidate cache

            return cache_data['data'], cache_data['cached_at']
        except (json.JSONDecodeError, KeyError):
            return None

    def save_universities(self, universities: dict, config: dict) -> None:
        """
        Save university list to cache.

        Args:
            universities: Dictionary of universities from PDF extraction
            config: Configuration used for this extraction
        """
        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'config': {
                'target_countries': config.get('target_countries'),
                'student_college': config.get('student_college'),
            },
            'data': universities
        }

        with open(self.universities_cache, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def get_mappings(self, countries: List[str], modules: List[str],
                     username: str) -> Optional[Tuple[dict, str]]:
        """
        Get cached module mapping data.

        Args:
            countries: List of country names
            modules: List of module codes
            username: NTU username

        Returns:
            Tuple of (mapping_dict, cache_timestamp) if valid cache exists,
            None otherwise
        """
        cache_key = self._generate_mapping_cache_key(countries, modules, username)
        cache_file = self.mappings_cache_dir / f"{cache_key}.json"

        if not self._is_cache_valid(cache_file, self.MAPPINGS_TTL):
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            return cache_data['data'], cache_data['cached_at']
        except (json.JSONDecodeError, KeyError):
            return None

    def save_mappings(self, mappings: dict, countries: List[str],
                      modules: List[str], username: str) -> None:
        """
        Save module mapping data to cache.

        Args:
            mappings: Dictionary of module mappings
            countries: List of country names
            modules: List of module codes
            username: NTU username
        """
        cache_key = self._generate_mapping_cache_key(countries, modules, username)
        cache_file = self.mappings_cache_dir / f"{cache_key}.json"

        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'countries': sorted(countries),
            'modules': sorted(modules),
            'username': username,
            'data': mappings
        }

        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def clear_all(self) -> List[str]:
        """
        Clear all cache files.

        Returns:
            List of cleared file names
        """
        cleared = []

        # Clear universities cache
        if self.universities_cache.exists():
            self.universities_cache.unlink()
            cleared.append('universities.json')

        # Clear all mapping caches
        for cache_file in self.mappings_cache_dir.glob('*.json'):
            cache_file.unlink()
            cleared.append(f'mappings/{cache_file.name}')

        return cleared

    def clear_universities(self) -> bool:
        """
        Clear only universities cache.

        Returns:
            True if cache was cleared, False if no cache existed
        """
        if self.universities_cache.exists():
            self.universities_cache.unlink()
            return True
        return False

    def clear_mappings(self) -> int:
        """
        Clear only mappings cache.

        Returns:
            Number of mapping cache files cleared
        """
        count = 0
        for cache_file in self.mappings_cache_dir.glob('*.json'):
            cache_file.unlink()
            count += 1
        return count

    def get_countries_universities(self) -> Optional[Tuple[Dict[str, List[str]], str]]:
        """
        Get cached country-university mapping.

        Cache TTL: 30 days (same as mappings, since this can change)

        Returns:
            Tuple of (countries_dict, cache_timestamp) if valid cache exists,
            None otherwise
        """
        cache_file = self.cache_dir / "countries_universities.json"

        if not self._is_cache_valid(cache_file, self.MAPPINGS_TTL):
            return None

        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)

            return cache_data['data'], cache_data['cached_at']
        except (json.JSONDecodeError, KeyError):
            return None

    def save_countries_universities(self, countries_universities: Dict[str, List[str]]) -> None:
        """
        Save country-university mapping to cache.

        Args:
            countries_universities: Dict mapping country -> list of universities
        """
        cache_file = self.cache_dir / "countries_universities.json"

        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'data': countries_universities,
            'total_countries': len(countries_universities),
            'total_universities': sum(len(unis) for unis in countries_universities.values())
        }

        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def clear_countries_universities(self) -> bool:
        """
        Clear only countries/universities cache.

        Returns:
            True if cache was cleared, False if no cache existed
        """
        cache_file = self.cache_dir / "countries_universities.json"
        if cache_file.exists():
            cache_file.unlink()
            return True
        return False
