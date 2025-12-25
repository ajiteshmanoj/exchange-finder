"""
NTU SSO Session Manager for authenticated access to module mapping system.
"""

import requests
from bs4 import BeautifulSoup
from typing import Tuple
import time


class NTUSession:
    """Manages authenticated session with NTU SSO and module mapping system."""

    def __init__(self, credentials: Tuple[str, str, str], login_url: str, student_id: str = None):
        """
        Initialize NTU session.

        Args:
            credentials: Tuple of (username, password, domain)
            login_url: SSO login URL
            student_id: Student matriculation number (optional)
        """
        self.username, self.password, self.domain = credentials
        self.login_url = login_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._authenticated = False
        self._student_id = student_id  # Use provided student ID if available
        self._target_page = None

    def login(self) -> bool:
        """
        Authenticate with NTU SSO.

        Returns:
            True if login successful, False otherwise
        """
        try:
            print("  Attempting to login to NTU SSO...")

            # First, get the login page to retrieve any tokens/hidden fields
            response = self.session.get(self.login_url)
            response.raise_for_status()

            # Parse the login form
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the form
            form = soup.find('form', {'name': 'frmLogin'})
            if not form:
                print("  ✗ Login form not found")
                return False

            # Get form action URL - should be sso_login2.asp
            from urllib.parse import urljoin, urlparse, parse_qs
            form_action = form.get('action', '')
            post_url = urljoin(response.url, form_action)

            # Prepare login data with correct field names
            login_data = {
                'UserName': self.username,
                'Password': self.password,
                'Domain': self.domain
            }

            # Find all hidden input fields and add them (includes p2, t, etc.)
            for hidden in form.find_all('input', type='hidden'):
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    login_data[name] = value

            # Extract target page from p2 parameter for later use
            target_page = login_data.get('p2', '')

            # Submit login form to sso_login2.asp
            print(f"    Logging in as {self.domain}\\{self.username}...")
            login_response = self.session.post(
                post_url,
                data=login_data,
                allow_redirects=True
            )

            # After successful login, we get redirected to blank.htm
            # This confirms login was successful
            if login_response.status_code == 200 and 'blank.htm' in login_response.url:
                self._authenticated = True
                self._target_page = target_page

                # Set student ID to provided value or fallback to username
                if not self._student_id:
                    self._student_id = self.username

                print("  ✓ Login successful!")
                print(f"    Student ID: {self._student_id}")
                return True

            # Fallback check for direct INSTEP page access
            elif 'instep_past_subj_matching' in login_response.url.lower():
                self._authenticated = True
                self._target_page = target_page

                # Try to extract student ID from URL
                if '?p1=' in login_response.url:
                    self._student_id = login_response.url.split('?p1=')[1].split('&')[0]
                elif not self._student_id:
                    self._student_id = self.username

                print("  ✓ Login successful!")
                print(f"    Student ID: {self._student_id}")
                return True

            print("  ✗ Login failed - unexpected response")
            print(f"    Response URL: {login_response.url}")
            return False

        except requests.exceptions.RequestException as e:
            print(f"  ✗ Login failed with error: {e}")
            return False
        except Exception as e:
            print(f"  ✗ Unexpected error during login: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if session is authenticated."""
        return self._authenticated

    @property
    def student_id(self) -> str:
        """Get the authenticated student ID."""
        return self._student_id or self.username

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Make authenticated GET request.

        Args:
            url: URL to request
            **kwargs: Additional arguments to pass to requests.get

        Returns:
            Response object
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call login() first.")

        return self.session.get(url, **kwargs)

    def post(self, url: str, data=None, **kwargs) -> requests.Response:
        """
        Make authenticated POST request.

        Args:
            url: URL to post to
            data: Data to post
            **kwargs: Additional arguments to pass to requests.post

        Returns:
            Response object
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call login() first.")

        return self.session.post(url, data=data, **kwargs)

    def close(self) -> None:
        """Close the session."""
        self.session.close()
        self._authenticated = False
