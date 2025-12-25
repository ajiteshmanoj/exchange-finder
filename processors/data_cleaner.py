"""
Data cleaning and normalization utilities for university data.
Handles university name variations and data standardization.
"""

import re
from typing import Dict, List


class UniversityNameNormalizer:
    """Normalize university names for matching across different data sources."""

    def __init__(self):
        # Common abbreviations to standardize
        self.abbreviations = {
            'univ.': 'university',
            'univ': 'university',
            'coll.': 'college',
            'coll': 'college',
            'inst.': 'institute',
            'inst': 'institute',
            'tech.': 'technology',
            'tech': 'technology',
            'u.': 'university',
            'uc': 'university college',
            'uit': 'university',
        }

        # Patterns to remove
        self.remove_patterns = [
            r'\([^)]*campus[^)]*\)',  # Remove (Campus Name)
            r'\([^)]*\)',  # Remove any other parentheses content
            r'\s*-\s*main\s*campus',  # Remove - Main Campus
            r'\s*-\s*.*\s*campus',  # Remove - Any Campus
        ]

    def normalize(self, name: str) -> str:
        """
        Normalize a university name to standard form.

        Args:
            name: Original university name

        Returns:
            Normalized university name
        """
        if not name:
            return ""

        # Convert to lowercase for processing
        normalized = name.lower().strip()

        # Remove "the" prefix
        normalized = re.sub(r'^the\s+', '', normalized)

        # Remove campus suffixes and parentheses
        for pattern in self.remove_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

        # Standardize abbreviations
        for abbr, full in self.abbreviations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(abbr) + r'\b'
            normalized = re.sub(pattern, full, normalized, flags=re.IGNORECASE)

        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Handle special cases with dashes
        normalized = re.sub(r'\s*-\s*', ' ', normalized)

        return normalized

    def get_base_name(self, name: str) -> str:
        """
        Get the base university name without qualifiers.

        Args:
            name: University name

        Returns:
            Base name for grouping
        """
        normalized = self.normalize(name)

        # Remove location specifiers at the end
        # e.g., "University of Sydney" → "university of sydney"
        # But keep "Sydney University" as is

        return normalized


class UniversityDataCleaner:
    """Clean and merge university data from multiple sources."""

    def __init__(self):
        self.normalizer = UniversityNameNormalizer()

    def group_university_variations(self, universities: Dict) -> Dict:
        """
        Group universities with multiple codes/campus variations.

        Args:
            universities: Dictionary of universities with different codes

        Returns:
            Grouped universities with combined data
        """
        # Create mapping of normalized names to university IDs
        name_to_ids = {}

        for uni_id, uni_data in universities.items():
            normalized_name = self.normalizer.normalize(uni_data['name'])

            if normalized_name not in name_to_ids:
                name_to_ids[normalized_name] = []

            name_to_ids[normalized_name].append(uni_id)

        # Merge variations
        merged_universities = {}
        processed_ids = set()

        for normalized_name, uni_ids in name_to_ids.items():
            # Use first ID as primary
            primary_id = uni_ids[0]

            if primary_id in processed_ids:
                continue

            # If single university, just copy it
            if len(uni_ids) == 1:
                merged_universities[primary_id] = universities[primary_id].copy()
                processed_ids.add(primary_id)
            else:
                # Merge multiple variations
                merged_data = self._merge_variations(
                    [universities[uid] for uid in uni_ids],
                    uni_ids
                )
                merged_universities[primary_id] = merged_data
                processed_ids.update(uni_ids)

        return merged_universities

    def _merge_variations(self, variations: List[Dict], uni_ids: List[str]) -> Dict:
        """
        Merge multiple university variations into one entry.

        Args:
            variations: List of university data dictionaries
            uni_ids: List of university IDs being merged

        Returns:
            Merged university data
        """
        # Start with first variation
        merged = variations[0].copy()

        # Use the shortest name (usually more canonical)
        merged['name'] = min([v['name'] for v in variations], key=len)

        # Aggregate sem1_spots (sum across all campuses)
        total_spots = sum(v.get('sem1_spots', 0) for v in variations)
        merged['sem1_spots'] = total_spots

        # Keep lowest min_cgpa requirement (most accessible)
        cgpa_values = [v.get('min_cgpa', 5.0) for v in variations if v.get('min_cgpa', 0) > 0]
        merged['min_cgpa'] = min(cgpa_values) if cgpa_values else 0.0

        # Combine university codes
        codes = [v.get('university_code', '') for v in variations if v.get('university_code')]
        merged['university_code'] = codes[0] if codes else ''
        merged['all_codes'] = list(set(codes))

        # Combine sub-codes
        sub_codes = [v.get('university_sub_code', '') for v in variations if v.get('university_sub_code')]
        merged['university_sub_code'] = sub_codes[0] if sub_codes else ''
        merged['all_sub_codes'] = list(set(sub_codes))

        # Combine remarks
        remarks = [v.get('remarks', '') for v in variations if v.get('remarks')]
        merged['remarks'] = ' | '.join(set(remarks)) if remarks else ''

        # Add variation count for reference
        merged['variation_count'] = len(variations)
        merged['merged_ids'] = uni_ids

        return merged

    def normalize_mapping_data(self, mapping_data: Dict) -> Dict:
        """
        Normalize university names in mapping data to match PDF data.

        Args:
            mapping_data: Raw mapping data from scraper

        Returns:
            Normalized mapping data
        """
        normalized = {}

        for uni_id, modules in mapping_data.items():
            # Normalize module mapping data
            normalized[uni_id] = {}

            for module_code, mappings in modules.items():
                normalized_mappings = []

                for mapping in mappings:
                    normalized_mapping = mapping.copy()

                    # Normalize university name in mapping
                    if 'university' in normalized_mapping:
                        normalized_mapping['university_normalized'] = \
                            self.normalizer.normalize(normalized_mapping['university'])

                    # Clean module names
                    if 'partner_module_name' in normalized_mapping:
                        normalized_mapping['partner_module_name'] = \
                            self._clean_module_name(normalized_mapping['partner_module_name'])

                    normalized_mappings.append(normalized_mapping)

                normalized[uni_id][module_code] = normalized_mappings

        return normalized

    def _clean_module_name(self, name: str) -> str:
        """
        Clean module name for display.

        Args:
            name: Raw module name

        Returns:
            Cleaned module name
        """
        if not name:
            return ""

        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', name.strip())

        # Remove common prefixes/suffixes that add no value
        cleaned = re.sub(r'\s*\(.*?\)\s*$', '', cleaned)

        return cleaned


def clean_and_group_universities(universities: Dict) -> Dict:
    """
    Main function to clean and group university data.

    Args:
        universities: Raw university dictionary

    Returns:
        Cleaned and grouped university dictionary
    """
    cleaner = UniversityDataCleaner()
    return cleaner.group_university_variations(universities)


def normalize_mappings(mapping_data: Dict) -> Dict:
    """
    Main function to normalize mapping data.

    Args:
        mapping_data: Raw mapping data

    Returns:
        Normalized mapping data
    """
    cleaner = UniversityDataCleaner()
    return cleaner.normalize_mapping_data(mapping_data)


if __name__ == "__main__":
    # Test normalization
    normalizer = UniversityNameNormalizer()

    test_names = [
        "The University of Queensland",
        "University of Queensland (St Lucia Campus)",
        "Univ. of Queensland",
        "National University of Ireland, Dublin",
        "Trinity Coll. Dublin",
        "Technical University of Denmark",
        "Tech. Univ. Denmark (DTU)",
    ]

    print("University Name Normalization Tests:\n")
    for name in test_names:
        normalized = normalizer.normalize(name)
        print(f"{name:50} → {normalized}")

    # Test grouping
    print("\n" + "="*80)
    print("University Grouping Test:\n")

    test_universities = {
        "AU-UQ": {
            "name": "University of Queensland",
            "country": "Australia",
            "university_code": "AU-UQ",
            "university_sub_code": "",
            "sem1_spots": 2,
            "min_cgpa": 3.5,
            "remarks": "Main campus"
        },
        "AU-UQ_SL": {
            "name": "University of Queensland (St Lucia)",
            "country": "Australia",
            "university_code": "AU-UQ",
            "university_sub_code": "SL",
            "sem1_spots": 1,
            "min_cgpa": 3.7,
            "remarks": "St Lucia campus"
        }
    }

    grouped = clean_and_group_universities(test_universities)

    for uni_id, uni_data in grouped.items():
        print(f"ID: {uni_id}")
        print(f"  Name: {uni_data['name']}")
        print(f"  Total Spots: {uni_data['sem1_spots']}")
        print(f"  Min CGPA: {uni_data['min_cgpa']}")
        print(f"  Variations: {uni_data.get('variation_count', 1)}")
        if 'merged_ids' in uni_data:
            print(f"  Merged IDs: {', '.join(uni_data['merged_ids'])}")
        print()
