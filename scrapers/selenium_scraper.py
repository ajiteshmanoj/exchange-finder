"""
Selenium-based NTU Module Mapping Scraper.
Handles SSO authentication and module mapping searches using browser automation.
"""

import os
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm


class SeleniumNTUScraper:
    """Selenium-based scraper for NTU module mappings with SSO authentication."""

    def __init__(self, credentials: Tuple[str, str, str], config: Dict, headless: bool = True):
        """
        Initialize Selenium scraper.

        Args:
            credentials: Tuple of (username, password, domain)
            config: Configuration dictionary
            headless: Run browser in headless mode (default True)
        """
        self.username, self.password, self.domain = credentials
        self.config = config
        self.headless = headless
        self.driver = None
        self._authenticated = False

        # Rate limiting
        self.delay_min = config.get('rate_limiting', {}).get('delay_min', 3.0)
        self.delay_max = config.get('rate_limiting', {}).get('delay_max', 5.0)

        # Approved years for filtering
        self.approved_years = config.get('approved_years', ['2024', '2025'])

        # URLs
        self.search_url = "https://wis.ntu.edu.sg/pls/lms/instep_past_subj_matching.show_rec2"
        self.login_check_url = "https://wis.ntu.edu.sg/pls/lms/instep_past_subj_matching.show_rec_INSTEP"

        # Checkpoint file
        self.checkpoint_file = "checkpoint.json"

    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with appropriate options."""
        options = Options()

        if self.headless:
            options.add_argument('--headless=new')

        # Standard options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        # Mimic real browser
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Enable cookies
        options.add_argument('--enable-cookies')

        # Disable automation flags
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # Set up driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Set timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(5)

        return driver

    def start(self) -> bool:
        """Start the browser and initialize session."""
        try:
            print("  Starting Chrome browser...")
            self.driver = self._setup_driver()
            print("  ✓ Browser started successfully")
            return True
        except Exception as e:
            print(f"  ✗ Failed to start browser: {e}")
            return False

    def login(self) -> bool:
        """
        Login to NTU SSO system.

        Returns:
            True if login successful, False otherwise
        """
        if not self.driver:
            if not self.start():
                return False

        try:
            # Use the SSO login URL with redirect to INSTEP page
            student_id = self.config.get('ntu_sso', {}).get('student_id', self.username)
            target_url = f"https://wis.ntu.edu.sg/pls/lms/instep_past_subj_matching.show_rec_INSTEP?p1={student_id}&p2="
            sso_url = f"https://sso.wis.ntu.edu.sg/webexe88/owa/sso_login1.asp?t=1&p2={target_url}"

            print(f"\n  Navigating to SSO login page...")
            self.driver.get(sso_url)
            time.sleep(2)

            # Dismiss any alert that might appear
            try:
                alert = self.driver.switch_to.alert
                alert.dismiss()
            except:
                pass

            # Check if we're on SSO login page
            current_url = self.driver.current_url

            if 'sso.wis.ntu.edu.sg' in current_url or 'sso_login' in current_url:
                print("  Detected SSO login page, entering credentials...")

                # Wait for login form
                wait = WebDriverWait(self.driver, 15)

                # STEP 1: Enter username and select domain
                try:
                    username_field = wait.until(
                        EC.presence_of_element_located((By.NAME, "UserName"))
                    )
                    username_field.clear()
                    username_field.send_keys(self.username)
                    print(f"    ✓ Entered username: {self.username}")
                except TimeoutException:
                    print("    ✗ Username field not found")
                    return False

                # Select domain
                try:
                    domain_select = Select(self.driver.find_element(By.NAME, "Domain"))
                    # Try to select by value first
                    try:
                        domain_select.select_by_value(self.domain.upper())
                    except:
                        # Try by visible text
                        for option in domain_select.options:
                            if self.domain.lower() in option.text.lower():
                                domain_select.select_by_visible_text(option.text)
                                break
                    print(f"    ✓ Selected domain: {self.domain}")
                except NoSuchElementException:
                    pass

                # Submit step 1
                try:
                    submit_btn = self.driver.find_element(By.NAME, "bOption")
                    submit_btn.click()
                except NoSuchElementException:
                    try:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                        submit_btn.click()
                    except:
                        self.driver.execute_script("document.forms[0].submit();")

                print("    Submitting username...")
                time.sleep(3)

                # STEP 2: Handle password page (could be Azure AD or NTU login)
                current_url = self.driver.current_url

                # Check for password field
                try:
                    # Wait for password field (various possible names)
                    password_field = None
                    possible_password_selectors = [
                        (By.NAME, "Password"),
                        (By.NAME, "password"),
                        (By.NAME, "passwd"),
                        (By.ID, "passwordInput"),
                        (By.ID, "i0118"),  # Microsoft login
                        (By.CSS_SELECTOR, "input[type='password']"),
                    ]

                    for selector_type, selector_value in possible_password_selectors:
                        try:
                            password_field = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((selector_type, selector_value))
                            )
                            if password_field:
                                break
                        except TimeoutException:
                            continue

                    if password_field:
                        password_field.clear()
                        password_field.send_keys(self.password)
                        print("    ✓ Entered password")

                        # Submit password
                        time.sleep(1)

                        # Try to find and click submit button
                        try:
                            # Microsoft login
                            submit_btn = self.driver.find_element(By.ID, "idSIButton9")
                            submit_btn.click()
                        except:
                            try:
                                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                                submit_btn.click()
                            except:
                                # Try pressing Enter
                                password_field.send_keys("\n")

                        print("    Submitting password...")

                        # Wait for redirect with retries (up to 30 seconds)
                        for wait_count in range(6):
                            time.sleep(5)

                            # Check for "Stay signed in?" or "Don't show again" dialogs
                            try:
                                stay_signed_in = self.driver.find_elements(By.ID, "idBtn_Back")
                                if stay_signed_in:
                                    stay_signed_in[0].click()
                                    print("      Clicked 'No' on stay signed in")
                                    time.sleep(2)
                            except:
                                pass

                            try:
                                dont_show = self.driver.find_elements(By.ID, "idSIButton9")
                                if dont_show:
                                    dont_show[0].click()
                                    print("      Clicked 'Yes' on stay signed in")
                                    time.sleep(2)
                            except:
                                pass

                            current_url = self.driver.current_url
                            # Check if we've left the SSO page
                            if 'instep' in current_url.lower() or 'show_rec' in current_url.lower() or 'blank.htm' in current_url.lower():
                                break
                            if 'sso' not in current_url.lower():
                                break
                            if wait_count < 5:
                                print(f"      Waiting for redirect... ({(wait_count+1)*5}s)")
                    else:
                        print("    ⚠️  No password field found, checking if already logged in...")

                except Exception as e:
                    print(f"    ⚠️  Password handling error: {e}")

                # Dismiss any alert that might appear
                try:
                    alert = self.driver.switch_to.alert
                    print(f"    Alert: {alert.text}")
                    alert.accept()
                    time.sleep(2)
                except:
                    pass

                # Handle potential 2FA/OTP
                current_url = self.driver.current_url
                if 'otp' in current_url.lower() or '2fa' in current_url.lower() or 'mfa' in current_url.lower():
                    print("\n  ⚠️  2FA/OTP detected!")
                    print("  Please complete 2FA in the browser window...")
                    print("  Waiting up to 2 minutes for 2FA completion...")

                    # Wait for 2FA to complete (up to 2 minutes)
                    for i in range(24):  # 24 * 5 seconds = 2 minutes
                        time.sleep(5)
                        current_url = self.driver.current_url
                        if 'instep' in current_url.lower() or 'wis.ntu.edu.sg/pls' in current_url:
                            print("  ✓ 2FA completed!")
                            break
                        if i == 23:
                            print("  ✗ 2FA timeout - please try again")
                            return False

                # Check for alerts again
                try:
                    alert = self.driver.switch_to.alert
                    print(f"    Alert: {alert.text}")
                    alert.accept()
                    time.sleep(2)
                except:
                    pass

                # Wait for redirect to complete
                time.sleep(3)

                # Check if login was successful
                current_url = self.driver.current_url
                print(f"    Current URL: {current_url[:80]}...")

                if 'instep' in current_url.lower() or 'show_rec' in current_url.lower():
                    self._authenticated = True
                    print("  ✓ Login successful!")

                    # Store the authenticated page URL
                    self._instep_url = current_url

                    return True
                elif 'blank.htm' in current_url.lower():
                    # The SSO redirected to blank.htm, which means login succeeded
                    # Now navigate to the target page
                    print("    Navigating to target page...")
                    self.driver.get(target_url)
                    time.sleep(3)

                    # Dismiss any alert
                    try:
                        alert = self.driver.switch_to.alert
                        alert.accept()
                    except:
                        pass

                    current_url = self.driver.current_url
                    if 'instep' in current_url.lower() or 'show_rec' in current_url.lower():
                        self._authenticated = True
                        self._instep_url = current_url
                        print("  ✓ Login successful!")
                        return True

                elif 'sso' in current_url.lower():
                    print("  ✗ Login failed - still on SSO page")
                    print(f"    Current URL: {current_url}")

                    # Check for error messages on NTU SSO page
                    try:
                        # NTU-specific error messages
                        page_source = self.driver.page_source.lower()
                        if 'invalid' in page_source:
                            print("    Error: Invalid credentials")
                        if 'incorrect' in page_source:
                            print("    Error: Incorrect username or password")
                        if 'locked' in page_source:
                            print("    Error: Account may be locked")

                        # Try to find any visible text that might be an error
                        body = self.driver.find_element(By.TAG_NAME, "body")
                        visible_text = body.text[:500] if body.text else ""
                        if visible_text:
                            print(f"    Page content: {visible_text[:200]}...")
                    except Exception as e:
                        print(f"    Could not read page: {e}")

                    # Check for generic error elements
                    try:
                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .alert, [class*='error'], font[color='red']")
                        for elem in error_elements:
                            if elem.text.strip():
                                print(f"    Error element: {elem.text.strip()}")
                    except:
                        pass

                    return False
                else:
                    # Try navigating to target anyway
                    print(f"  ⚠️  Unexpected page, trying target URL...")
                    self.driver.get(target_url)
                    time.sleep(3)

                    try:
                        alert = self.driver.switch_to.alert
                        alert.accept()
                    except:
                        pass

                    self._authenticated = True
                    return True

            elif 'instep' in current_url.lower() or 'wis.ntu.edu.sg/pls' in current_url:
                # Already logged in
                self._authenticated = True
                print("  ✓ Already logged in!")
                return True

            else:
                print(f"  ⚠️  Unexpected page: {current_url}")
                return False

        except TimeoutException:
            print("  ✗ Login timeout")
            return False
        except Exception as e:
            print(f"  ✗ Login error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _check_session(self) -> bool:
        """Check if session is still valid, re-login if needed."""
        if not self._authenticated:
            return self.login()

        # Don't aggressively check URL - just return True if we think we're authenticated
        # We'll handle actual session expiry when it happens during operations
        return True

    def _ensure_on_search_page(self) -> bool:
        """Navigate to search page if needed, re-login if session expired."""
        try:
            current_url = self.driver.current_url

            # If we're already on the search page, we're good
            if 'instep' in current_url.lower() or 'show_rec' in current_url.lower():
                return True

            # If we're on SSO page, we need to re-login
            if 'sso' in current_url.lower():
                print("\n  ⚠️  Session expired, re-logging in...")
                self._authenticated = False
                return self.login()

            # Otherwise, navigate to search page
            student_id = self.config.get('ntu_sso', {}).get('student_id', self.username)
            search_url = f"https://wis.ntu.edu.sg/pls/lms/instep_past_subj_matching.show_rec_INSTEP?p1={student_id}&p2="
            self.driver.get(search_url)
            time.sleep(2)

            # Dismiss any alert
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except:
                pass

            return True

        except Exception as e:
            print(f"  ⚠️  Error ensuring search page: {e}")
            return False

    def search_university_mappings(self, university_name: str, country: str) -> Dict[str, List[Dict]]:
        """
        Search for ALL module mappings for a university.

        This is more efficient than searching module by module - we get all
        mappings in one request and filter by target modules.

        Args:
            university_name: Partner university name
            country: Country name

        Returns:
            Dictionary mapping module code -> list of mappings
        """
        if not self._check_session():
            print(f"      ✗ Session invalid for {university_name}")
            return {}

        try:
            # Get the INSTEP page URL with student ID
            student_id = self.config.get('ntu_sso', {}).get('student_id', self.username)
            instep_url = f"https://wis.ntu.edu.sg/pls/lms/instep_past_subj_matching.show_rec_INSTEP?p1={student_id}&p2="

            # Navigate to the search page
            self.driver.get(instep_url)

            wait = WebDriverWait(self.driver, 10)

            # Dismiss any alert
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except:
                pass

            # Wait for form to load
            time.sleep(2)

            # Step 1: Select country
            try:
                country_select = Select(wait.until(
                    EC.presence_of_element_located((By.NAME, "which_cty"))
                ))
                # Find matching country by value (uppercase)
                country_upper = country.upper()
                try:
                    country_select.select_by_value(country_upper)
                except:
                    # Try by visible text
                    for option in country_select.options:
                        if country.lower() in option.text.lower():
                            country_select.select_by_visible_text(option.text)
                            break

                time.sleep(2)  # Wait for university dropdown to update

            except Exception as e:
                print(f"      Warning: Could not select country {country}: {e}")
                return {}

            # Step 2: Select university (re-fetch element after page update)
            try:
                uni_select = Select(self.driver.find_element(By.NAME, "which_uni_val"))
                uni_found = False

                # Get all option texts first to avoid stale element
                options_data = [(opt.text.strip(), opt.get_attribute('value')) for opt in uni_select.options]

                for opt_text, opt_value in options_data:
                    if university_name.lower() in opt_text.lower():
                        # Re-fetch the select element to avoid stale reference
                        uni_select = Select(self.driver.find_element(By.NAME, "which_uni_val"))
                        uni_select.select_by_visible_text(opt_text)
                        uni_found = True
                        time.sleep(1)
                        break

                if not uni_found:
                    # Try partial match
                    for opt_text, opt_value in options_data:
                        # Match first few words
                        uni_words = university_name.lower().split()[:2]
                        if all(word in opt_text.lower() for word in uni_words):
                            uni_select = Select(self.driver.find_element(By.NAME, "which_uni_val"))
                            uni_select.select_by_visible_text(opt_text)
                            uni_found = True
                            time.sleep(1)
                            break

                if not uni_found:
                    return {}

            except Exception as e:
                print(f"      Warning: Could not select university {university_name}: {e}")
                return {}

            # Step 3: Keep course as "ALL" to get all mappings
            try:
                course_select = Select(self.driver.find_element(By.NAME, "which_course"))
                course_select.select_by_value("ALL")
            except:
                pass  # Already set to ALL by default

            # Step 4: Submit search
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Submit']")
                submit_btn.click()
            except NoSuchElementException:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                    submit_btn.click()
                except:
                    self.driver.execute_script("document.forms[0].submit();")

            # Wait for results
            time.sleep(3)

            # Dismiss any alert
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except:
                pass

            # Parse all results
            all_mappings = self._parse_results()

            # Group by NTU module code
            result = {}
            for mapping in all_mappings:
                module_code = mapping.get('ntu_module', '').upper()
                if module_code:
                    if module_code not in result:
                        result[module_code] = []
                    result[module_code].append(mapping)

            return result

        except Exception as e:
            print(f"      Warning: Search failed for {university_name}: {e}")
            return {}

    def scrape_countries_and_universities(self) -> Dict[str, List[str]]:
        """
        Scrape ALL countries and universities from NTU dropdown.

        Target URL: https://wis.ntu.edu.sg/pls/lms/instep_past_subj_matching.show_rec2

        Returns:
            Dictionary mapping country_name -> list of university_names
            Example: {
                "Australia": ["University of Melbourne", "University of Sydney", ...],
                "Denmark": ["University of Copenhagen", "Aarhus University", ...],
                ...
            }
        """
        if not self._check_session():
            raise RuntimeError("Session invalid - cannot scrape countries")

        try:
            # Navigate to search page with student ID
            student_id = self.config.get('ntu_sso', {}).get('student_id', self.username)
            instep_url = f"https://wis.ntu.edu.sg/pls/lms/instep_past_subj_matching.show_rec_INSTEP?p1={student_id}&p2="

            self.driver.get(instep_url)
            time.sleep(2)

            # Dismiss any alert
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except:
                pass

            wait = WebDriverWait(self.driver, 10)

            # Find country dropdown and extract values FIRST (before any selections)
            # This avoids stale element references
            country_select = Select(wait.until(
                EC.presence_of_element_located((By.NAME, "which_cty"))
            ))

            # Extract all country values and texts into a list (not element references)
            country_data = []
            for option in country_select.options[1:]:  # Skip first placeholder
                value = option.get_attribute('value')
                text = option.text.strip()
                if value and value != "":
                    country_data.append((value, text))

            countries_universities = {}

            print(f"\n  Scraping countries and universities from NTU dropdown...")
            print(f"  Found {len(country_data)} countries")

            for country_value, country_text in tqdm(country_data, desc="  Processing countries", unit="country"):
                try:
                    # Re-find the dropdown element each time (avoids stale reference)
                    country_select = Select(self.driver.find_element(By.NAME, "which_cty"))
                    country_select.select_by_value(country_value)
                    time.sleep(1.5)  # Wait for university dropdown to update

                    # Get university dropdown (name="which_uni_val")
                    uni_select = Select(self.driver.find_element(By.NAME, "which_uni_val"))

                    # Extract universities (skip first placeholder option)
                    universities = []
                    for uni_option in uni_select.options[1:]:
                        uni_text = uni_option.text.strip()
                        if uni_text:
                            universities.append(uni_text)

                    countries_universities[country_text] = universities

                except Exception as e:
                    print(f"\n    Warning: Failed to get universities for {country_text}: {e}")
                    countries_universities[country_text] = []

                # Rate limiting
                time.sleep(random.uniform(0.5, 1.0))

            print(f"\n  ✓ Scraped {len(countries_universities)} countries")
            print(f"  ✓ Total universities: {sum(len(unis) for unis in countries_universities.values())}")

            return countries_universities

        except Exception as e:
            print(f"  ✗ Failed to scrape countries/universities: {e}")
            raise RuntimeError(f"Country/university scraping failed: {e}")

    def search_module_mapping(self, ntu_module: str, university_name: str, country: str = None) -> List[Dict]:
        """
        Search for module mappings using the web form.

        Note: This is kept for compatibility but search_university_mappings is more efficient.

        Args:
            ntu_module: NTU module code (e.g., 'SC4001')
            university_name: Partner university name
            country: Country name (optional, for selecting in dropdown)

        Returns:
            List of approved mappings
        """
        # Use the university-wide search and filter
        all_mappings = self.search_university_mappings(university_name, country or "")
        return all_mappings.get(ntu_module.upper(), [])

    def _parse_results(self) -> List[Dict]:
        """
        Parse search results from the current page.

        The results table has the following structure (discovered from HTML):
        - Column 0-1: NTU Course Code (colspan="2")
        - Column 2: NTU Course Name
        - Column 3: NTU Course Type
        - Column 4: Foreign Course Code
        - Column 5: Foreign Course Name
        - Column 6: AU (Academic Units)
        - Column 7: Status (Approved/Rejected)
        - Column 8: Year
        - Column 9: Sem
        """
        mappings = []

        try:
            # Find all rows with course data (class="row0" or "row1")
            rows = self.driver.find_elements(By.CSS_SELECTOR, "tr.row0, tr.row1")

            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")

                # Skip rows with too few columns (likely detail rows)
                if len(cols) < 8:
                    continue

                try:
                    # Check for colspan in first column (indicates data row)
                    first_col_span = cols[0].get_attribute('colspan')

                    if first_col_span == '2':
                        # This is a data row with NTU Course Code in colspan=2
                        # Columns: [NTU Code(2), NTU Name, NTU Type, Foreign Code, Foreign Name, AU, Status, Year, Sem]
                        ntu_code = cols[0].text.strip()
                        ntu_name = cols[1].text.strip() if len(cols) > 1 else ''
                        ntu_type = cols[2].text.strip() if len(cols) > 2 else ''
                        partner_code = cols[3].text.strip() if len(cols) > 3 else ''
                        partner_name = cols[4].text.strip() if len(cols) > 4 else ''
                        au = cols[5].text.strip() if len(cols) > 5 else ''
                        status = cols[6].text.strip() if len(cols) > 6 else ''
                        year = cols[7].text.strip() if len(cols) > 7 else ''
                        sem = cols[8].text.strip() if len(cols) > 8 else ''

                        # Only include approved mappings from recent years
                        if 'approved' in status.lower():
                            if any(y in year for y in self.approved_years):
                                mappings.append({
                                    'ntu_module': ntu_code,
                                    'ntu_module_name': ntu_name,
                                    'ntu_module_type': ntu_type,
                                    'partner_module_code': partner_code,
                                    'partner_module_name': partner_name,
                                    'academic_units': au,
                                    'status': status,
                                    'approval_year': year,
                                    'semester': sem
                                })

                except (StaleElementReferenceException, IndexError):
                    continue

        except Exception as e:
            # Try alternative parsing using page source
            try:
                page_source = self.driver.page_source

                # Quick regex-based fallback
                import re

                # Pattern to match data rows
                pattern = r'<tr class="row[01]"[^>]*>\s*<td[^>]*colspan="2"[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]*)</td>'

                matches = re.findall(pattern, page_source, re.DOTALL)

                for match in matches:
                    ntu_code = match[0].strip()
                    ntu_name = match[1].strip()
                    ntu_type = match[2].strip()
                    partner_code = match[3].strip()
                    partner_name = match[4].strip()
                    au = match[5].strip()
                    status = match[6].strip()
                    year = match[7].strip()
                    sem = match[8].strip() if len(match) > 8 else ''

                    if 'approved' in status.lower():
                        if any(y in year for y in self.approved_years):
                            mappings.append({
                                'ntu_module': ntu_code,
                                'ntu_module_name': ntu_name,
                                'ntu_module_type': ntu_type,
                                'partner_module_code': partner_code,
                                'partner_module_name': partner_name,
                                'academic_units': au,
                                'status': status,
                                'approval_year': year,
                                'semester': sem
                            })

            except Exception:
                pass  # Fallback also failed

        return mappings

    def scrape_all_mappings(self, universities: Dict, modules: List[str]) -> Dict:
        """
        Scrape module mappings for all universities.

        This method searches for ALL mappings for each university in one request,
        then filters by target modules. This is much more efficient than searching
        module by module.

        Args:
            universities: Dictionary of universities from PDF
            modules: List of target module codes

        Returns:
            Dictionary mapping university_id -> module -> list of mappings
        """
        # Load checkpoint if exists
        mapping_data, completed_universities = self._load_checkpoint()

        # Normalize target modules to uppercase
        target_modules = set(m.upper() for m in modules)

        print(f"\n  Searching module mappings for {len(universities)} universities...")
        print(f"  Target modules: {', '.join(sorted(target_modules))}")

        if completed_universities:
            print(f"  Resuming from checkpoint: {len(completed_universities)} universities already completed")

        remaining_unis = {k: v for k, v in universities.items() if k not in completed_universities}
        print(f"  Universities to process: {len(remaining_unis)}")

        # One search per university (not per module)
        estimated_time = len(remaining_unis) * (self.delay_min + self.delay_max) / 2 / 60
        print(f"  Estimated time: {estimated_time:.1f} minutes\n")

        successful_module_matches = 0
        universities_with_mappings = 0
        universities_processed = 0

        # Create progress bar
        with tqdm(total=len(remaining_unis), desc="  Processing universities", unit="univ") as pbar:
            for uni_id, uni_info in remaining_unis.items():
                uni_name = uni_info['name']
                country = uni_info.get('country', '')

                if uni_id not in mapping_data:
                    mapping_data[uni_id] = {}

                # Search for ALL mappings for this university
                all_uni_mappings = self._retry_university_search(uni_name, country)

                # Filter to only target modules
                found_count = 0
                for module in target_modules:
                    mappings = all_uni_mappings.get(module, [])
                    mapping_data[uni_id][module] = mappings

                    if mappings:
                        found_count += 1
                        successful_module_matches += 1

                if found_count > 0:
                    universities_with_mappings += 1

                # Update progress
                pbar.set_postfix({
                    'university': uni_name[:25],
                    'found': f"{found_count}/{len(target_modules)}"
                })

                universities_processed += 1
                pbar.update(1)

                # Save checkpoint every 5 universities
                if universities_processed % 5 == 0:
                    completed_universities.add(uni_id)
                    self._save_checkpoint(mapping_data, completed_universities)

                # Mark as completed
                completed_universities.add(uni_id)

                # Rate limiting between universities
                delay = random.uniform(self.delay_min, self.delay_max)
                time.sleep(delay)

        # Final checkpoint save
        self._save_checkpoint(mapping_data, completed_universities)

        print(f"\n  ✓ Search complete!")
        print(f"    Total universities processed: {len(universities)}")
        print(f"    Universities with mappings: {universities_with_mappings}")
        print(f"    Total module matches found: {successful_module_matches}")

        return mapping_data

    def _retry_university_search(self, university_name: str, country: str, max_retries: int = 3) -> Dict[str, List[Dict]]:
        """Search university with retry logic and exponential backoff."""
        for attempt in range(max_retries):
            try:
                mappings = self.search_university_mappings(university_name, country)
                return mappings

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"\n      Retry {attempt + 1}/{max_retries} for {university_name} (waiting {wait_time}s)")
                    time.sleep(wait_time)

                    # Check session
                    self._check_session()
                else:
                    print(f"\n      Failed after {max_retries} attempts: {university_name}")
                    return {}

        return {}

    def _retry_search(self, ntu_module: str, university_name: str, max_retries: int = 3) -> List[Dict]:
        """Search with retry logic and exponential backoff."""
        for attempt in range(max_retries):
            try:
                mappings = self.search_module_mapping(ntu_module, university_name)
                return mappings

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"\n      Retry {attempt + 1}/{max_retries} for {ntu_module} at {university_name} (waiting {wait_time}s)")
                    time.sleep(wait_time)

                    # Check session
                    self._check_session()
                else:
                    print(f"\n      Failed after {max_retries} attempts: {ntu_module} at {university_name}")
                    return []

        return []

    def _load_checkpoint(self) -> Tuple[Dict, set]:
        """Load checkpoint from file if exists."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    mapping_data = data.get('mapping_data', {})
                    completed = set(data.get('completed_universities', []))
                    print(f"  ✓ Loaded checkpoint: {len(completed)} universities completed")
                    return mapping_data, completed
            except Exception as e:
                print(f"  ⚠️  Failed to load checkpoint: {e}")

        return {}, set()

    def _save_checkpoint(self, mapping_data: Dict, completed_universities: set) -> None:
        """Save checkpoint to file."""
        try:
            checkpoint = {
                'mapping_data': mapping_data,
                'completed_universities': list(completed_universities),
                'timestamp': datetime.now().isoformat()
            }
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
        except Exception as e:
            print(f"  ⚠️  Failed to save checkpoint: {e}")

    def clear_checkpoint(self) -> None:
        """Clear checkpoint file."""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            print("  ✓ Checkpoint cleared")

    def close(self) -> None:
        """Close the browser and clean up."""
        if self.driver:
            try:
                self.driver.quit()
                print("  ✓ Browser closed")
            except:
                pass
            self.driver = None
            self._authenticated = False

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated


def run_selenium_scraper(credentials: Tuple[str, str, str],
                         config: Dict,
                         universities: Dict,
                         modules: List[str],
                         headless: bool = True) -> Dict:
    """
    Main function to run the Selenium scraper.

    Args:
        credentials: NTU login credentials
        config: Configuration dictionary
        universities: Universities from PDF extraction
        modules: Target module codes
        headless: Run in headless mode

    Returns:
        Dictionary of mapping data
    """
    scraper = SeleniumNTUScraper(credentials, config, headless=headless)

    try:
        # Login
        if not scraper.login():
            print("  ✗ Login failed!")
            return {}

        # Scrape mappings
        mapping_data = scraper.scrape_all_mappings(universities, modules)

        return mapping_data

    except KeyboardInterrupt:
        print("\n  ⚠️  Interrupted by user")
        return {}

    except Exception as e:
        print(f"  ✗ Scraper error: {e}")
        return {}

    finally:
        scraper.close()


if __name__ == "__main__":
    # Test the Selenium scraper
    import yaml
    from utils.crypto import CredentialManager
    from scrapers.pdf_extractor import extract_and_filter_universities

    print("="*80)
    print("SELENIUM SCRAPER TEST")
    print("="*80)

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Get credentials
    creds = CredentialManager().decrypt_credentials()

    # Test with just the first university
    pdf_path = config['pdf_file']
    universities = extract_and_filter_universities(pdf_path, config)

    # Limit to first 2 universities for testing
    test_unis = dict(list(universities.items())[:2])
    test_modules = config['target_modules'][:2]

    print(f"\nTesting with {len(test_unis)} universities and {len(test_modules)} modules")

    # Run scraper (headed mode for testing)
    mapping_data = run_selenium_scraper(
        creds,
        config,
        test_unis,
        test_modules,
        headless=False  # Show browser for debugging
    )

    print(f"\n✓ Test complete!")
    print(f"  Results: {json.dumps(mapping_data, indent=2)}")
