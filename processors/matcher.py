"""
Data matching utilities to combine PDF university data with module mapping data.
"""

from typing import Dict, List, Set
from processors.data_cleaner import UniversityNameNormalizer


class UniversityMatcher:
    """Match and combine university data from different sources."""

    def __init__(self):
        self.normalizer = UniversityNameNormalizer()

    def match_pdf_to_mappings(self, pdf_data: Dict, mapping_data: Dict) -> Dict:
        """
        Combine PDF university data with module mapping data.

        Args:
            pdf_data: Dictionary from PDF extraction {uni_id: uni_info}
            mapping_data: Dictionary from module scraping {uni_id: {module: [mappings]}}

        Returns:
            Integrated dataset with structure:
            {
                'university_id': {
                    'name': str,
                    'country': str,
                    'sem1_spots': int,
                    'min_cgpa': float,
                    'university_code': str,
                    'mappable_modules': {
                        'SC4001': [list of mappings],
                        'SC4002': [list of mappings],
                        ...
                    },
                    'mappable_count': int,
                    'unmappable_modules': [list of module codes],
                    'coverage_score': float,  # percentage of modules mappable
                    'remarks': str
                }
            }
        """
        integrated_data = {}

        for uni_id, uni_info in pdf_data.items():
            # Get mapping data for this university (if available)
            uni_mappings = mapping_data.get(uni_id, {})

            # Separate mappable and unmappable modules
            mappable_modules = {}
            unmappable_modules = []

            for module_code, mappings in uni_mappings.items():
                if mappings and len(mappings) > 0:
                    mappable_modules[module_code] = mappings
                else:
                    unmappable_modules.append(module_code)

            # Calculate coverage score
            total_modules = len(uni_mappings)
            mappable_count = len(mappable_modules)
            coverage_score = (mappable_count / total_modules * 100) if total_modules > 0 else 0.0

            # Build integrated entry
            integrated_data[uni_id] = {
                # Basic info from PDF
                'name': uni_info['name'],
                'country': uni_info['country'],
                'sem1_spots': uni_info.get('sem1_spots', 0),
                'min_cgpa': uni_info.get('min_cgpa', 0.0),
                'university_code': uni_info.get('university_code', ''),
                'university_sub_code': uni_info.get('university_sub_code', ''),
                'remarks': uni_info.get('remarks', ''),

                # Mapping data
                'mappable_modules': mappable_modules,
                'mappable_count': mappable_count,
                'unmappable_modules': unmappable_modules,
                'coverage_score': coverage_score,

                # Additional metadata
                'all_codes': uni_info.get('all_codes', [uni_info.get('university_code', '')]),
                'variation_count': uni_info.get('variation_count', 1),
            }

        return integrated_data

    def get_mapping_summary(self, mappings: List[Dict]) -> str:
        """
        Create a readable summary of module mappings.

        Args:
            mappings: List of mapping dictionaries

        Returns:
            Formatted string summarizing the mappings
        """
        if not mappings:
            return "No mappings found"

        # Get unique partner modules (in case of duplicates)
        unique_modules = {}
        for mapping in mappings:
            code = mapping.get('partner_module_code', 'Unknown')
            name = mapping.get('partner_module_name', '')

            if code not in unique_modules:
                unique_modules[code] = name

        # Format as "CODE (Name)" or just "CODE" if no name
        summary_parts = []
        for code, name in unique_modules.items():
            if name:
                summary_parts.append(f"{code} ({name})")
            else:
                summary_parts.append(code)

        return "; ".join(summary_parts)

    def get_detailed_mapping_info(self, mappings: List[Dict]) -> List[str]:
        """
        Get detailed information about each mapping.

        Args:
            mappings: List of mapping dictionaries

        Returns:
            List of formatted mapping strings
        """
        if not mappings:
            return []

        details = []
        for mapping in mappings:
            code = mapping.get('partner_module_code', 'Unknown')
            name = mapping.get('partner_module_name', '')
            year = mapping.get('approval_year', '')

            if name:
                detail = f"{code} - {name}"
            else:
                detail = code

            if year:
                detail += f" (Approved: {year})"

            details.append(detail)

        return details

    def calculate_module_statistics(self, integrated_data: Dict) -> Dict:
        """
        Calculate statistics about module mappings across all universities.

        Args:
            integrated_data: Integrated university data

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_universities': len(integrated_data),
            'by_country': {},
            'module_availability': {},
            'avg_mappable_modules': 0.0,
            'universities_by_coverage': {
                '100%': 0,
                '75-99%': 0,
                '50-74%': 0,
                '25-49%': 0,
                '0-24%': 0,
            }
        }

        # Collect all module codes
        all_modules = set()
        for uni_data in integrated_data.values():
            all_modules.update(uni_data['mappable_modules'].keys())
            all_modules.update(uni_data['unmappable_modules'])

        # Initialize module availability counter
        for module in all_modules:
            stats['module_availability'][module] = {
                'available_at': 0,
                'not_available_at': 0
            }

        # Process each university
        total_mappable = 0
        for uni_data in integrated_data.values():
            country = uni_data['country']
            mappable_count = uni_data['mappable_count']
            coverage = uni_data['coverage_score']

            # Country stats
            if country not in stats['by_country']:
                stats['by_country'][country] = {
                    'count': 0,
                    'avg_mappable': 0.0,
                    'total_spots': 0
                }

            stats['by_country'][country]['count'] += 1
            stats['by_country'][country]['total_spots'] += uni_data['sem1_spots']

            # Module availability
            for module in all_modules:
                if module in uni_data['mappable_modules']:
                    stats['module_availability'][module]['available_at'] += 1
                else:
                    stats['module_availability'][module]['not_available_at'] += 1

            # Coverage distribution
            if coverage == 100:
                stats['universities_by_coverage']['100%'] += 1
            elif coverage >= 75:
                stats['universities_by_coverage']['75-99%'] += 1
            elif coverage >= 50:
                stats['universities_by_coverage']['50-74%'] += 1
            elif coverage >= 25:
                stats['universities_by_coverage']['25-49%'] += 1
            else:
                stats['universities_by_coverage']['0-24%'] += 1

            total_mappable += mappable_count

        # Calculate averages
        if len(integrated_data) > 0:
            stats['avg_mappable_modules'] = total_mappable / len(integrated_data)

            # Average mappable per country
            for country_stats in stats['by_country'].values():
                if country_stats['count'] > 0:
                    total_country_mappable = sum(
                        uni['mappable_count']
                        for uni in integrated_data.values()
                        if uni['country'] == country_stats.get('country', '')
                    )
                    country_stats['avg_mappable'] = total_country_mappable / country_stats['count']

        return stats


def combine_data_sources(pdf_data: Dict, mapping_data: Dict) -> Dict:
    """
    Main function to combine PDF and mapping data.

    Args:
        pdf_data: University data from PDF
        mapping_data: Module mapping data from scraper

    Returns:
        Integrated dataset
    """
    matcher = UniversityMatcher()
    return matcher.match_pdf_to_mappings(pdf_data, mapping_data)


def get_statistics(integrated_data: Dict) -> Dict:
    """
    Get statistics about the integrated data.

    Args:
        integrated_data: Combined university data

    Returns:
        Statistics dictionary
    """
    matcher = UniversityMatcher()
    return matcher.calculate_module_statistics(integrated_data)


if __name__ == "__main__":
    # Test matching logic
    print("Testing University Matcher\n")
    print("="*80)

    # Sample PDF data
    sample_pdf_data = {
        "AU-UQ": {
            "name": "University of Queensland",
            "country": "Australia",
            "university_code": "AU-UQ",
            "university_sub_code": "",
            "sem1_spots": 3,
            "min_cgpa": 3.5,
            "remarks": "Group of Eight member"
        },
        "DK-DTU": {
            "name": "Technical University of Denmark",
            "country": "Denmark",
            "university_code": "DK-DTU",
            "university_sub_code": "",
            "sem1_spots": 2,
            "min_cgpa": 3.7,
            "remarks": ""
        }
    }

    # Sample mapping data
    sample_mapping_data = {
        "AU-UQ": {
            "SC4001": [
                {
                    "ntu_module": "SC4001",
                    "partner_module_code": "COMP3308",
                    "partner_module_name": "Introduction to Artificial Intelligence",
                    "university": "University of Queensland",
                    "status": "Approved",
                    "approval_year": "2024"
                }
            ],
            "SC4002": [
                {
                    "ntu_module": "SC4002",
                    "partner_module_code": "COMP3420",
                    "partner_module_name": "Natural Language Processing",
                    "university": "University of Queensland",
                    "status": "Approved",
                    "approval_year": "2025"
                }
            ],
            "SC4062": [],  # No mapping
            "SC4021": [],
            "SC4023": [],
            "SC4003": []
        },
        "DK-DTU": {
            "SC4001": [
                {
                    "ntu_module": "SC4001",
                    "partner_module_code": "02456",
                    "partner_module_name": "Deep Learning",
                    "university": "Technical University of Denmark",
                    "status": "Approved",
                    "approval_year": "2024"
                }
            ],
            "SC4002": [],
            "SC4062": [],
            "SC4021": [],
            "SC4023": [],
            "SC4003": []
        }
    }

    # Test matching
    integrated = combine_data_sources(sample_pdf_data, sample_mapping_data)

    print("\nIntegrated Data:\n")
    for uni_id, uni_data in integrated.items():
        print(f"{uni_id}: {uni_data['name']}")
        print(f"  Country: {uni_data['country']}")
        print(f"  Spots: {uni_data['sem1_spots']}, Min CGPA: {uni_data['min_cgpa']}")
        print(f"  Mappable modules: {uni_data['mappable_count']}/6 ({uni_data['coverage_score']:.1f}%)")
        print(f"  Can map: {list(uni_data['mappable_modules'].keys())}")
        print(f"  Cannot map: {uni_data['unmappable_modules']}")
        print()

    # Test statistics
    print("="*80)
    print("\nStatistics:\n")
    stats = get_statistics(integrated)
    print(f"Total universities: {stats['total_universities']}")
    print(f"Average mappable modules: {stats['avg_mappable_modules']:.1f}")
    print(f"\nBy country:")
    for country, country_stats in stats['by_country'].items():
        print(f"  {country}: {country_stats['count']} universities")
    print(f"\nModule availability:")
    for module, avail in stats['module_availability'].items():
        total = avail['available_at'] + avail['not_available_at']
        pct = (avail['available_at'] / total * 100) if total > 0 else 0
        print(f"  {module}: {avail['available_at']}/{total} ({pct:.0f}%)")
