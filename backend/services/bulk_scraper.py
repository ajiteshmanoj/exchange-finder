"""
Bulk Scraper Service for NTU Exchange Module Mappings

Orchestrates full scraping of all countries, universities, and module mappings,
storing results directly to SQLite database for instant user queries.
"""

import time
import random
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple, Callable, Optional, Any
from pathlib import Path

from backend.services.database import DatabaseManager
from scrapers.selenium_scraper import SeleniumNTUScraper


class BulkScraper:
    """
    Orchestrates full scraping of all NTU exchange module mappings.

    This scraper:
    1. Logs in once to NTU SSO
    2. Scrapes all countries and universities from dropdowns
    3. For each university, gets ALL module mappings
    4. Stores everything in SQLite database
    5. Reports progress via callbacks for real-time updates
    """

    def __init__(
        self,
        credentials: Tuple[str, str, str],
        config: Dict,
        progress_callback: Callable[[Dict], None] = None,
        headless: bool = True
    ):
        """
        Initialize bulk scraper.

        Args:
            credentials: Tuple of (username, password, domain)
            config: Configuration dictionary
            progress_callback: Optional callback for progress updates
            headless: Run browser in headless mode
        """
        self.credentials = credentials
        self.config = config
        self.progress_callback = progress_callback or (lambda x: None)
        self.headless = headless

        self.db = DatabaseManager()
        self.scraper = None
        self.job_id = None
        self._cancelled = False

    def _send_progress(self, **kwargs):
        """Send progress update via callback."""
        try:
            self.progress_callback(kwargs)
        except Exception as e:
            print(f"  Warning: Progress callback failed: {e}")

    def cancel(self):
        """Cancel the running scrape job."""
        self._cancelled = True
        if self.job_id:
            self.db.update_scrape_job(
                self.job_id,
                status='cancelled',
                error_message='Cancelled by user'
            )

    def scrape_all(self) -> Dict[str, Any]:
        """
        Execute full scrape of all countries, universities, and mappings.

        Returns:
            Dictionary with scrape results and statistics
        """
        self._cancelled = False
        start_time = datetime.now()

        # Use existing job_id if set (from admin.py), otherwise create new one
        if self.job_id is None:
            self.job_id = self.db.create_scrape_job()

        self._send_progress(
            type='started',
            job_id=self.job_id,
            message='Starting full scrape...'
        )

        try:
            # Initialize scraper
            self.scraper = SeleniumNTUScraper(
                self.credentials,
                self.config,
                headless=self.headless
            )

            # Step 1: Login
            self._send_progress(type='status', message='Logging in to NTU SSO...')
            if not self.scraper.login():
                raise RuntimeError("Login failed - check credentials")

            self._send_progress(type='status', message='Login successful!')

            # Step 2: Get all countries and universities
            self._send_progress(type='status', message='Fetching countries and universities...')
            countries_universities = self.scraper.scrape_countries_and_universities()

            if self._cancelled:
                return self._cancelled_result()

            # Calculate totals
            total_countries = len(countries_universities)
            total_universities = sum(
                len(unis) for unis in countries_universities.values()
            )

            self.db.update_scrape_job(
                self.job_id,
                total_countries=total_countries,
                total_universities=total_universities
            )

            self._send_progress(
                type='discovery',
                total_countries=total_countries,
                total_universities=total_universities,
                message=f'Found {total_countries} countries, {total_universities} universities'
            )

            # Step 3: Clear existing data (fresh scrape)
            self._send_progress(type='status', message='Clearing existing data...')
            self.db.clear_all_data()

            # Step 4: Scrape mappings for each university
            completed_countries = 0
            completed_universities = 0
            total_mappings = 0

            for country_name, universities in countries_universities.items():
                if self._cancelled:
                    return self._cancelled_result()

                # Insert country
                country_id = self.db.insert_country(country_name)

                self.db.update_scrape_job(
                    self.job_id,
                    current_country=country_name,
                    completed_countries=completed_countries
                )

                self._send_progress(
                    type='country_start',
                    country=country_name,
                    universities_count=len(universities),
                    completed_countries=completed_countries,
                    total_countries=total_countries
                )

                for university_name in universities:
                    if self._cancelled:
                        return self._cancelled_result()

                    # Skip "ALL" option
                    if university_name.upper() == 'ALL':
                        continue

                    self.db.update_scrape_job(
                        self.job_id,
                        current_university=university_name,
                        completed_universities=completed_universities
                    )

                    self._send_progress(
                        type='university_start',
                        country=country_name,
                        university=university_name,
                        completed_universities=completed_universities,
                        total_universities=total_universities
                    )

                    try:
                        # Insert university
                        university_id = self.db.insert_university(
                            country_id,
                            university_name
                        )

                        # Scrape ALL mappings for this university
                        all_mappings = self.scraper.search_university_mappings(
                            university_name,
                            country_name
                        )

                        # Flatten mappings and insert
                        mappings_list = []
                        for module_code, mappings in all_mappings.items():
                            mappings_list.extend(mappings)

                        if mappings_list:
                            count = self.db.insert_mappings_bulk(
                                university_id,
                                mappings_list
                            )
                            total_mappings += count

                            self._send_progress(
                                type='university_complete',
                                country=country_name,
                                university=university_name,
                                mappings_found=count
                            )
                        else:
                            self._send_progress(
                                type='university_complete',
                                country=country_name,
                                university=university_name,
                                mappings_found=0
                            )

                    except Exception as e:
                        print(f"  Warning: Failed to scrape {university_name}: {e}")
                        self._send_progress(
                            type='university_error',
                            country=country_name,
                            university=university_name,
                            error=str(e)
                        )

                    completed_universities += 1

                    # Rate limiting
                    delay = random.uniform(
                        self.config.get('rate_limiting', {}).get('delay_min', 2.0),
                        self.config.get('rate_limiting', {}).get('delay_max', 3.0)
                    )
                    time.sleep(delay)

                completed_countries += 1

                self._send_progress(
                    type='country_complete',
                    country=country_name,
                    completed_countries=completed_countries,
                    total_countries=total_countries
                )

            # Scrape complete
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.db.update_scrape_job(
                self.job_id,
                status='completed',
                completed_countries=total_countries,
                completed_universities=completed_universities
            )

            result = {
                'status': 'completed',
                'job_id': self.job_id,
                'total_countries': total_countries,
                'total_universities': completed_universities,
                'total_mappings': total_mappings,
                'duration_seconds': duration,
                'started_at': start_time.isoformat(),
                'completed_at': end_time.isoformat()
            }

            self._send_progress(
                type='completed',
                **result
            )

            return result

        except Exception as e:
            error_msg = str(e)
            self.db.update_scrape_job(
                self.job_id,
                status='failed',
                error_message=error_msg
            )

            self._send_progress(
                type='error',
                job_id=self.job_id,
                error=error_msg
            )

            return {
                'status': 'failed',
                'job_id': self.job_id,
                'error': error_msg
            }

        finally:
            if self.scraper:
                self.scraper.close()

    def _cancelled_result(self) -> Dict[str, Any]:
        """Return result for cancelled scrape."""
        return {
            'status': 'cancelled',
            'job_id': self.job_id,
            'message': 'Scrape was cancelled by user'
        }


class AsyncBulkScraper:
    """
    Async wrapper for BulkScraper to run in background thread.

    Provides asyncio-compatible interface for FastAPI integration.
    """

    def __init__(
        self,
        credentials: Tuple[str, str, str],
        config: Dict,
        headless: bool = True
    ):
        self.credentials = credentials
        self.config = config
        self.headless = headless
        self._scraper = None
        self._progress_queue = asyncio.Queue()
        self._task = None

    async def start(self) -> int:
        """
        Start scraping in background thread.

        Returns:
            Job ID
        """
        import concurrent.futures

        def progress_callback(data):
            try:
                asyncio.get_event_loop().call_soon_threadsafe(
                    self._progress_queue.put_nowait,
                    data
                )
            except Exception:
                pass  # Queue might be closed

        self._scraper = BulkScraper(
            self.credentials,
            self.config,
            progress_callback=progress_callback,
            headless=self.headless
        )

        # Run in thread pool
        loop = asyncio.get_event_loop()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._task = loop.run_in_executor(executor, self._scraper.scrape_all)

        # Wait for job_id to be set
        while self._scraper.job_id is None:
            await asyncio.sleep(0.1)

        return self._scraper.job_id

    async def get_progress(self, timeout: float = 30.0) -> Optional[Dict]:
        """Get next progress update."""
        try:
            return await asyncio.wait_for(
                self._progress_queue.get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None

    async def cancel(self):
        """Cancel the running scrape."""
        if self._scraper:
            self._scraper.cancel()

    async def wait(self) -> Dict[str, Any]:
        """Wait for scrape to complete and return result."""
        if self._task:
            return await self._task
        return {'status': 'not_started'}


# Convenience function for running scrape
def run_full_scrape(
    credentials: Tuple[str, str, str],
    config: Dict,
    progress_callback: Callable[[Dict], None] = None,
    headless: bool = True
) -> Dict[str, Any]:
    """
    Run a full scrape of all module mappings.

    Args:
        credentials: NTU login credentials (username, password, domain)
        config: Configuration dictionary
        progress_callback: Optional callback for progress updates
        headless: Run browser in headless mode

    Returns:
        Dictionary with scrape results
    """
    scraper = BulkScraper(
        credentials,
        config,
        progress_callback=progress_callback,
        headless=headless
    )
    return scraper.scrape_all()


if __name__ == "__main__":
    # Test the bulk scraper
    import yaml
    from utils.crypto import CredentialManager

    print("="*80)
    print("BULK SCRAPER TEST")
    print("="*80)

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Get credentials
    creds = CredentialManager().decrypt_credentials()

    def progress_handler(data):
        msg_type = data.get('type', 'unknown')
        if msg_type == 'university_complete':
            print(f"  ✓ {data.get('university', 'Unknown')}: {data.get('mappings_found', 0)} mappings")
        elif msg_type == 'country_complete':
            print(f"\n  Country complete: {data.get('country', 'Unknown')}")
        elif msg_type == 'error':
            print(f"  ✗ Error: {data.get('error', 'Unknown error')}")
        elif msg_type == 'completed':
            print(f"\n  ✓ Scrape complete!")
            print(f"    Countries: {data.get('total_countries', 0)}")
            print(f"    Universities: {data.get('total_universities', 0)}")
            print(f"    Mappings: {data.get('total_mappings', 0)}")
            print(f"    Duration: {data.get('duration_seconds', 0):.1f} seconds")

    # Run scrape (headed mode for testing)
    result = run_full_scrape(
        creds,
        config,
        progress_callback=progress_handler,
        headless=False  # Show browser for debugging
    )

    print(f"\nResult: {result}")
