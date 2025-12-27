"""
SQLite Database Manager for NTU Exchange Module Mappings

Provides persistent storage for pre-scraped module mappings,
enabling instant user searches without live scraping.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager


class DatabaseManager:
    """
    Manages SQLite database for storing pre-scraped module mappings.

    Tables:
        - countries: All NTU exchange partner countries
        - universities: All partner universities
        - module_mappings: Approved module mappings
        - scrape_jobs: Track scrape progress/status
    """

    def __init__(self, db_path: str = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Defaults to data/exchange_mappings.db
        """
        if db_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.db_path = project_root / "data" / "exchange_mappings.db"
        else:
            self.db_path = Path(db_path)

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Countries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS countries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Universities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS universities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    dropdown_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (country_id) REFERENCES countries(id),
                    UNIQUE(country_id, name)
                )
            ''')

            # Module mappings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS module_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    university_id INTEGER NOT NULL,
                    ntu_module_code TEXT NOT NULL,
                    ntu_module_name TEXT,
                    ntu_module_type TEXT,
                    partner_module_code TEXT,
                    partner_module_name TEXT,
                    academic_units TEXT,
                    status TEXT,
                    approval_year TEXT,
                    semester TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (university_id) REFERENCES universities(id)
                )
            ''')

            # Scrape jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scrape_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT DEFAULT 'pending',
                    total_countries INTEGER DEFAULT 0,
                    completed_countries INTEGER DEFAULT 0,
                    total_universities INTEGER DEFAULT 0,
                    completed_universities INTEGER DEFAULT 0,
                    current_country TEXT,
                    current_university TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT
                )
            ''')

            # Create indexes for fast querying
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_mappings_ntu_module
                ON module_mappings(ntu_module_code)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_mappings_university
                ON module_mappings(university_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_universities_country
                ON universities(country_id)
            ''')

    # ==================== Country Operations ====================

    def insert_country(self, name: str) -> int:
        """
        Insert a country, returning its ID. If exists, return existing ID.

        Args:
            name: Country name

        Returns:
            Country ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Try to insert, ignore if exists
            cursor.execute('''
                INSERT OR IGNORE INTO countries (name) VALUES (?)
            ''', (name,))

            # Get the ID (whether just inserted or existing)
            cursor.execute('SELECT id FROM countries WHERE name = ?', (name,))
            return cursor.fetchone()['id']

    def get_all_countries(self) -> List[str]:
        """Get all country names."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM countries ORDER BY name')
            return [row['name'] for row in cursor.fetchall()]

    def get_country_id(self, name: str) -> Optional[int]:
        """Get country ID by name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM countries WHERE name = ?', (name,))
            row = cursor.fetchone()
            return row['id'] if row else None

    # ==================== University Operations ====================

    def insert_university(self, country_id: int, name: str, dropdown_value: str = None) -> int:
        """
        Insert a university, returning its ID. If exists, return existing ID.

        Args:
            country_id: Foreign key to countries table
            name: University name
            dropdown_value: Value from NTU dropdown (for scraping)

        Returns:
            University ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO universities (country_id, name, dropdown_value)
                VALUES (?, ?, ?)
            ''', (country_id, name, dropdown_value))

            cursor.execute('''
                SELECT id FROM universities WHERE country_id = ? AND name = ?
            ''', (country_id, name))
            return cursor.fetchone()['id']

    def get_universities_by_country(self, country_name: str) -> List[str]:
        """Get all university names for a country."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.name
                FROM universities u
                JOIN countries c ON u.country_id = c.id
                WHERE c.name = ?
                ORDER BY u.name
            ''', (country_name,))
            return [row['name'] for row in cursor.fetchall()]

    def get_university_id(self, country_name: str, university_name: str) -> Optional[int]:
        """Get university ID by country and name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.id
                FROM universities u
                JOIN countries c ON u.country_id = c.id
                WHERE c.name = ? AND u.name = ?
            ''', (country_name, university_name))
            row = cursor.fetchone()
            return row['id'] if row else None

    # ==================== Module Mapping Operations ====================

    def insert_mapping(self, university_id: int, mapping: Dict[str, Any]) -> int:
        """
        Insert a module mapping.

        Args:
            university_id: Foreign key to universities table
            mapping: Dictionary with mapping fields

        Returns:
            Mapping ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO module_mappings (
                    university_id, ntu_module_code, ntu_module_name, ntu_module_type,
                    partner_module_code, partner_module_name, academic_units,
                    status, approval_year, semester
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                university_id,
                mapping.get('ntu_module', mapping.get('ntu_module_code', '')),
                mapping.get('ntu_module_name', ''),
                mapping.get('ntu_module_type', ''),
                mapping.get('partner_module_code', ''),
                mapping.get('partner_module_name', ''),
                mapping.get('academic_units', ''),
                mapping.get('status', ''),
                mapping.get('approval_year', ''),
                mapping.get('semester', '')
            ))

            return cursor.lastrowid

    def insert_mappings_bulk(self, university_id: int, mappings: List[Dict[str, Any]]) -> int:
        """
        Insert multiple mappings for a university.

        Args:
            university_id: Foreign key to universities table
            mappings: List of mapping dictionaries

        Returns:
            Number of mappings inserted
        """
        if not mappings:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            data = [
                (
                    university_id,
                    m.get('ntu_module', m.get('ntu_module_code', '')),
                    m.get('ntu_module_name', ''),
                    m.get('ntu_module_type', ''),
                    m.get('partner_module_code', ''),
                    m.get('partner_module_name', ''),
                    m.get('academic_units', ''),
                    m.get('status', ''),
                    m.get('approval_year', ''),
                    m.get('semester', '')
                )
                for m in mappings
            ]

            cursor.executemany('''
                INSERT INTO module_mappings (
                    university_id, ntu_module_code, ntu_module_name, ntu_module_type,
                    partner_module_code, partner_module_name, academic_units,
                    status, approval_year, semester
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)

            return len(data)

    def get_mappings_by_modules(
        self,
        module_codes: List[str],
        countries: List[str] = None
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Get all mappings for specified modules, optionally filtered by countries.

        Args:
            module_codes: List of NTU module codes (e.g., ['SC4001', 'SC4002'])
            countries: Optional list of countries to filter by

        Returns:
            Nested dict: {university_key: {module_code: [mappings]}}
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build query
            placeholders = ','.join('?' * len(module_codes))
            query = f'''
                SELECT
                    c.name as country,
                    u.name as university,
                    u.id as university_id,
                    m.*
                FROM module_mappings m
                JOIN universities u ON m.university_id = u.id
                JOIN countries c ON u.country_id = c.id
                WHERE UPPER(m.ntu_module_code) IN ({placeholders})
            '''
            params = [code.upper() for code in module_codes]

            if countries:
                country_placeholders = ','.join('?' * len(countries))
                query += f' AND c.name IN ({country_placeholders})'
                params.extend(countries)

            query += ' ORDER BY c.name, u.name, m.ntu_module_code'

            cursor.execute(query, params)

            # Group results by university
            results = {}
            for row in cursor.fetchall():
                # Create a unique key for university
                uni_key = f"{row['country']}_{row['university']}"

                if uni_key not in results:
                    results[uni_key] = {
                        'country': row['country'],
                        'university': row['university'],
                        'mappings': {}
                    }

                module_code = row['ntu_module_code'].upper()
                if module_code not in results[uni_key]['mappings']:
                    results[uni_key]['mappings'][module_code] = []

                results[uni_key]['mappings'][module_code].append({
                    'ntu_module': row['ntu_module_code'],
                    'ntu_module_name': row['ntu_module_name'],
                    'ntu_module_type': row['ntu_module_type'],
                    'partner_module_code': row['partner_module_code'],
                    'partner_module_name': row['partner_module_name'],
                    'academic_units': row['academic_units'],
                    'status': row['status'],
                    'approval_year': row['approval_year'],
                    'semester': row['semester']
                })

            return results

    def get_all_module_codes(self) -> List[str]:
        """Get all unique NTU module codes in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT UPPER(ntu_module_code) as code
                FROM module_mappings
                ORDER BY code
            ''')
            return [row['code'] for row in cursor.fetchall()]

    def clear_mappings_for_university(self, university_id: int):
        """Delete all mappings for a university (before re-scraping)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM module_mappings WHERE university_id = ?',
                (university_id,)
            )

    # ==================== Scrape Job Operations ====================

    def create_scrape_job(self) -> int:
        """Create a new scrape job and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scrape_jobs (status, started_at)
                VALUES ('running', ?)
            ''', (datetime.now().isoformat(),))
            return cursor.lastrowid

    def update_scrape_job(
        self,
        job_id: int,
        total_countries: int = None,
        completed_countries: int = None,
        total_universities: int = None,
        completed_universities: int = None,
        current_country: str = None,
        current_university: str = None,
        status: str = None,
        error_message: str = None
    ):
        """Update scrape job progress."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if total_countries is not None:
                updates.append('total_countries = ?')
                params.append(total_countries)
            if completed_countries is not None:
                updates.append('completed_countries = ?')
                params.append(completed_countries)
            if total_universities is not None:
                updates.append('total_universities = ?')
                params.append(total_universities)
            if completed_universities is not None:
                updates.append('completed_universities = ?')
                params.append(completed_universities)
            if current_country is not None:
                updates.append('current_country = ?')
                params.append(current_country)
            if current_university is not None:
                updates.append('current_university = ?')
                params.append(current_university)
            if status is not None:
                updates.append('status = ?')
                params.append(status)
                if status in ('completed', 'failed', 'cancelled'):
                    updates.append('completed_at = ?')
                    params.append(datetime.now().isoformat())
            if error_message is not None:
                updates.append('error_message = ?')
                params.append(error_message)

            if updates:
                params.append(job_id)
                cursor.execute(
                    f'UPDATE scrape_jobs SET {", ".join(updates)} WHERE id = ?',
                    params
                )

    def get_scrape_job(self, job_id: int) -> Optional[Dict]:
        """Get scrape job status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM scrape_jobs WHERE id = ?', (job_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_latest_scrape_job(self) -> Optional[Dict]:
        """Get the most recent scrape job."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM scrape_jobs
                ORDER BY id DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_running_scrape_job(self) -> Optional[Dict]:
        """Get currently running scrape job if any."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM scrape_jobs
                WHERE status = 'running'
                ORDER BY id DESC LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def force_cancel_stale_jobs(self) -> int:
        """
        Force-cancel any jobs stuck in 'running' state.
        Use when the server was restarted and scraper processes are gone.

        Returns:
            Number of jobs cancelled
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scrape_jobs
                SET status = 'cancelled',
                    error_message = 'Force cancelled - server restarted or process died',
                    completed_at = ?
                WHERE status = 'running'
            ''', (datetime.now().isoformat(),))
            return cursor.rowcount

    # ==================== Statistics ====================

    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM countries')
            total_countries = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM universities')
            total_universities = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM module_mappings')
            total_mappings = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(DISTINCT ntu_module_code) FROM module_mappings')
            unique_modules = cursor.fetchone()[0]

            # Get last scrape info
            last_job = self.get_latest_scrape_job()
            last_scrape = None
            if last_job and last_job.get('status') == 'completed':
                last_scrape = last_job.get('completed_at')

            return {
                'populated': total_mappings > 0,
                'total_countries': total_countries,
                'total_universities': total_universities,
                'total_mappings': total_mappings,
                'unique_modules': unique_modules,
                'last_scrape': last_scrape,
                'db_path': str(self.db_path)
            }

    def is_populated(self) -> bool:
        """Check if database has been populated with mappings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM module_mappings')
            return cursor.fetchone()[0] > 0

    # ==================== Cleanup ====================

    def clear_all_data(self):
        """Clear all data from database (for fresh scrape)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM module_mappings')
            cursor.execute('DELETE FROM universities')
            cursor.execute('DELETE FROM countries')
            # Keep scrape_jobs for history

    def clear_mappings_only(self):
        """Clear only mappings (keep countries/universities structure)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM module_mappings')
