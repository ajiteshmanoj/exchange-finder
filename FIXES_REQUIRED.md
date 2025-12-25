# Remaining Fixes Required

This document tracks known issues and improvements needed for the NTU Exchange Scraper.

---

## Critical Issues

### 1. Session Management During Search (Repeated Logins)

**Problem:** During module mapping searches, the scraper repeatedly logs in even though a valid session exists. This causes:
- Excessive login attempts to NTU SSO
- Slow search performance
- Potential rate limiting or account lockout

**Root Cause:** The `_check_session()` method and navigation logic don't properly maintain session state when navigating between different NTU INSTEP pages.

**Files Affected:**
- `scrapers/selenium_scraper.py`

**Fix Required:**
1. Complete the `_ensure_on_search_page()` method implementation
2. Replace aggressive `_check_session()` calls with smarter session handling
3. Use URL-based navigation checks only when necessary
4. Integrate `_ensure_on_search_page()` into `search_module_mappings()` and `scrape_countries_and_universities()`

**Suggested Implementation:**
```python
def _ensure_on_search_page(self) -> bool:
    """Navigate to search page if needed, re-login if session expired."""
    target_url = "https://wis.ntu.edu.sg/pls/lms/instep_past_subj_matching.show_rec2"

    try:
        current_url = self.driver.current_url

        # Already on the right page
        if "instep_past_subj_matching" in current_url:
            return True

        # On SSO page - session expired, need to re-login
        if "ntu.edu.sg/cas/" in current_url or "login" in current_url.lower():
            self._authenticated = False
            return self.login()

        # On different NTU page - navigate to search page
        self.driver.get(target_url + f"?p_stu_id={self.username}")
        time.sleep(2)

        # Verify navigation succeeded
        if "instep_past_subj_matching" in self.driver.current_url:
            return True

        # If redirected to login, session expired
        if "ntu.edu.sg/cas/" in self.driver.current_url:
            self._authenticated = False
            return self.login()

        return True

    except Exception as e:
        print(f"Error ensuring search page: {e}")
        return False
```

---

## Medium Priority

### 2. Country Selector Loading State

**Problem:** When the cache is empty, loading countries takes 2-5 minutes. The UI shows a loading spinner but could provide better progress feedback.

**Improvement:** Add WebSocket support for country scraping progress, similar to the search progress.

**Files Affected:**
- `frontend/src/components/CountrySelector.jsx`
- `backend/api/main.py`

---

### 3. Error Handling for Universities Not in PDF

**Problem:** Universities scraped from NTU website that aren't in the PDF don't have spots/CGPA data.

**Current Behavior:** These show as "Unknown" which is correct.

**Improvement:** Add visual indicator in results to distinguish between "0 spots" vs "Unknown spots".

**Files Affected:**
- `backend/processors/matcher.py`
- `frontend/src/components/Results.jsx` (if exists)

---

## Low Priority

### 4. Module Input Validation

**Problem:** Users can input invalid module codes (e.g., wrong format).

**Improvement:** Add client-side validation for NTU module code format (e.g., `XX####` pattern).

**Files Affected:**
- `frontend/src/components/ModuleSelector.jsx`

---

### 5. Cache Timestamp Display

**Problem:** Cache timestamps shown in UI are in ISO format, not human-readable.

**Improvement:** Format as "2 days ago" or "Dec 25, 2025 at 10:30 AM".

**Files Affected:**
- `frontend/src/components/CountrySelector.jsx`
- `frontend/src/components/Search.jsx`

---

## Completed Features

- [x] Dynamic country selection (all NTU exchange partnerships)
- [x] Searchable multi-select dropdown for countries
- [x] Dynamic module input (users can add any modules)
- [x] NTU SSO login verification
- [x] Combined login + country fetch in single session
- [x] 30-day caching for countries/universities
- [x] Removed hardcoded country and module lists
- [x] Fixed stale element reference during country scraping

---

## Testing Checklist

- [ ] Login with valid NTU credentials
- [ ] Login with invalid credentials (should show error)
- [ ] First-time country load (cache empty) - should take 2-5 min
- [ ] Second country load (cached) - should be instant
- [ ] Search with 1 country, 1 module
- [ ] Search with 10+ countries, 3+ modules
- [ ] Search should NOT require repeated logins
- [ ] WebSocket progress updates during search
- [ ] Results display correctly with mappings

---

## Environment Notes

- Backend: FastAPI + Uvicorn (Python 3.x)
- Frontend: React 18 + Tailwind CSS + react-select
- Browser Automation: Selenium WebDriver (Chrome/Chromium)
- Tested on: macOS (Darwin 25.1.0)
