"""
University ranking and filtering utilities.
Ranks universities based on multiple criteria.
"""

from typing import Dict, List, Tuple
from operator import itemgetter


class UniversityRanker:
    """Rank and filter universities based on configurable criteria."""

    def __init__(self, min_mappable_modules: int = 2):
        """
        Initialize ranker.

        Args:
            min_mappable_modules: Minimum number of mappable modules required
        """
        self.min_mappable_modules = min_mappable_modules

    def filter_minimum_mappings(self, data: Dict) -> Dict:
        """
        Filter universities that meet minimum mappable module requirement.

        Args:
            data: Integrated university data

        Returns:
            Filtered dictionary with only qualifying universities
        """
        filtered = {}

        for uni_id, uni_data in data.items():
            if uni_data['mappable_count'] >= self.min_mappable_modules:
                filtered[uni_id] = uni_data

        return filtered

    def rank_universities(self, data: Dict) -> List[Tuple[str, Dict]]:
        """
        Rank universities by multiple criteria.

        Ranking order (in priority):
        1. Country (alphabetical)
        2. Number of mappable modules (descending)
        3. Number of Sem 1 spots (descending)
        4. Min CGPA requirement (ascending - lower is better)

        Args:
            data: University data dictionary

        Returns:
            List of (university_id, university_data) tuples, sorted by rank
        """
        # Convert to list of tuples for sorting
        universities = list(data.items())

        # Sort with multiple keys
        # Python's sort is stable, so we sort in reverse order of priority
        ranked = sorted(
            universities,
            key=lambda x: (
                x[1]['country'],           # Primary: Country (A-Z)
                -x[1]['mappable_count'],   # Secondary: Mappable modules (high to low)
                -x[1]['sem1_spots'],       # Tertiary: Spots (high to low)
                x[1]['min_cgpa']           # Quaternary: CGPA (low to high)
            )
        )

        return ranked

    def get_top_universities(self, data: Dict, top_n: int = 15) -> List[Tuple[str, Dict]]:
        """
        Get top N universities overall (ignoring country grouping).

        Args:
            data: University data
            top_n: Number of top universities to return

        Returns:
            List of top universities
        """
        # Rank by mappable modules, then spots, then CGPA
        ranked = sorted(
            data.items(),
            key=lambda x: (
                -x[1]['mappable_count'],
                -x[1]['sem1_spots'],
                x[1]['min_cgpa']
            )
        )

        return ranked[:top_n]

    def group_by_country(self, ranked_data: List[Tuple[str, Dict]]) -> Dict[str, List[Tuple[str, Dict]]]:
        """
        Group ranked universities by country.

        Args:
            ranked_data: List of (uni_id, uni_data) tuples

        Returns:
            Dictionary mapping country -> list of universities
        """
        by_country = {}

        for uni_id, uni_data in ranked_data:
            country = uni_data['country']

            if country not in by_country:
                by_country[country] = []

            by_country[country].append((uni_id, uni_data))

        return by_country

    def get_country_summary(self, data: Dict) -> Dict[str, Dict]:
        """
        Get summary statistics for each country.

        Args:
            data: University data

        Returns:
            Dictionary mapping country -> summary stats
        """
        summary = {}

        for uni_data in data.values():
            country = uni_data['country']

            if country not in summary:
                summary[country] = {
                    'count': 0,
                    'total_spots': 0,
                    'avg_mappable': 0.0,
                    'avg_cgpa': 0.0,
                    'min_cgpa': float('inf'),
                    'max_cgpa': 0.0,
                    'universities': []
                }

            summary[country]['count'] += 1
            summary[country]['total_spots'] += uni_data['sem1_spots']
            summary[country]['universities'].append(uni_data['name'])

            # Track CGPA ranges
            cgpa = uni_data['min_cgpa']
            if cgpa > 0:  # Ignore 0 values
                summary[country]['min_cgpa'] = min(summary[country]['min_cgpa'], cgpa)
                summary[country]['max_cgpa'] = max(summary[country]['max_cgpa'], cgpa)

        # Calculate averages
        for country, stats in summary.items():
            if stats['count'] > 0:
                # Average mappable modules
                total_mappable = sum(
                    uni['mappable_count']
                    for uni in data.values()
                    if uni['country'] == country
                )
                stats['avg_mappable'] = total_mappable / stats['count']

                # Average CGPA
                cgpa_values = [
                    uni['min_cgpa']
                    for uni in data.values()
                    if uni['country'] == country and uni['min_cgpa'] > 0
                ]
                if cgpa_values:
                    stats['avg_cgpa'] = sum(cgpa_values) / len(cgpa_values)

                # Handle case where no valid CGPA found
                if stats['min_cgpa'] == float('inf'):
                    stats['min_cgpa'] = 0.0

        # Sort universities alphabetically in each country
        for stats in summary.values():
            stats['universities'].sort()

        return summary

    def calculate_scores(self, data: Dict) -> Dict:
        """
        Calculate composite scores for universities (for alternative ranking).

        Scoring criteria:
        - Mappable modules: 40 points (max)
        - Sem 1 spots: 30 points (max)
        - CGPA requirement: 30 points (max) - lower CGPA = higher score

        Args:
            data: University data

        Returns:
            Dictionary with scores added to each university
        """
        scored_data = {}

        # Find max values for normalization
        max_mappable = max((uni['mappable_count'] for uni in data.values()), default=6)
        max_spots = max((uni['sem1_spots'] for uni in data.values()), default=10)
        max_cgpa = 5.0  # NTU scale

        for uni_id, uni_data in data.items():
            # Copy data
            scored_uni = uni_data.copy()

            # Calculate component scores
            mappable_score = (uni_data['mappable_count'] / max_mappable) * 40 if max_mappable > 0 else 0
            spots_score = (uni_data['sem1_spots'] / max_spots) * 30 if max_spots > 0 else 0

            # CGPA score: lower is better, so invert
            cgpa = uni_data['min_cgpa']
            cgpa_score = ((max_cgpa - cgpa) / max_cgpa) * 30 if cgpa > 0 else 30

            # Total score
            total_score = mappable_score + spots_score + cgpa_score

            scored_uni['score_breakdown'] = {
                'mappable_score': round(mappable_score, 2),
                'spots_score': round(spots_score, 2),
                'cgpa_score': round(cgpa_score, 2),
                'total_score': round(total_score, 2)
            }

            scored_data[uni_id] = scored_uni

        return scored_data


def filter_and_rank(data: Dict, min_mappable: int = 2) -> List[Tuple[str, Dict]]:
    """
    Main function to filter and rank universities.

    Args:
        data: Integrated university data
        min_mappable: Minimum mappable modules required

    Returns:
        Ranked list of universities
    """
    ranker = UniversityRanker(min_mappable_modules=min_mappable)
    filtered = ranker.filter_minimum_mappings(data)
    ranked = ranker.rank_universities(filtered)
    return ranked


def get_top_n(data: Dict, n: int = 15) -> List[Tuple[str, Dict]]:
    """
    Get top N universities.

    Args:
        data: University data
        n: Number of top universities

    Returns:
        List of top universities
    """
    ranker = UniversityRanker()
    return ranker.get_top_universities(data, top_n=n)


def summarize_by_country(data: Dict) -> Dict[str, Dict]:
    """
    Get country-level summary statistics.

    Args:
        data: University data

    Returns:
        Country summary dictionary
    """
    ranker = UniversityRanker()
    return ranker.get_country_summary(data)


if __name__ == "__main__":
    # Test ranking logic
    print("Testing University Ranker\n")
    print("="*80)

    # Sample data
    sample_data = {
        "AU-UQ": {
            "name": "University of Queensland",
            "country": "Australia",
            "sem1_spots": 3,
            "min_cgpa": 3.5,
            "mappable_count": 4,
            "coverage_score": 66.7,
            "mappable_modules": {},
            "unmappable_modules": []
        },
        "AU-MELB": {
            "name": "University of Melbourne",
            "country": "Australia",
            "sem1_spots": 2,
            "min_cgpa": 3.7,
            "mappable_count": 5,
            "coverage_score": 83.3,
            "mappable_modules": {},
            "unmappable_modules": []
        },
        "DK-DTU": {
            "name": "Technical University of Denmark",
            "country": "Denmark",
            "sem1_spots": 2,
            "min_cgpa": 3.6,
            "mappable_count": 3,
            "coverage_score": 50.0,
            "mappable_modules": {},
            "unmappable_modules": []
        },
        "SE-KTH": {
            "name": "KTH Royal Institute of Technology",
            "country": "Sweden",
            "sem1_spots": 4,
            "min_cgpa": 3.4,
            "mappable_count": 4,
            "coverage_score": 66.7,
            "mappable_modules": {},
            "unmappable_modules": []
        },
        "FI-AALTO": {
            "name": "Aalto University",
            "country": "Finland",
            "sem1_spots": 1,
            "min_cgpa": 3.5,
            "mappable_count": 2,
            "coverage_score": 33.3,
            "mappable_modules": {},
            "unmappable_modules": []
        },
    }

    # Test filtering
    ranker = UniversityRanker(min_mappable_modules=2)
    filtered = ranker.filter_minimum_mappings(sample_data)
    print(f"Filtered universities (min 2 mappable): {len(filtered)}/{len(sample_data)}\n")

    # Test ranking
    ranked = ranker.rank_universities(filtered)
    print("Ranked universities (by country, mappable, spots, CGPA):\n")
    for i, (uni_id, uni_data) in enumerate(ranked, 1):
        print(f"{i:2}. [{uni_data['country']:12}] {uni_data['name']:40} | "
              f"Mappable: {uni_data['mappable_count']}, "
              f"Spots: {uni_data['sem1_spots']}, "
              f"CGPA: {uni_data['min_cgpa']:.2f}")

    # Test top universities
    print("\n" + "="*80)
    print("\nTop 3 Universities Overall:\n")
    top = ranker.get_top_universities(filtered, top_n=3)
    for i, (uni_id, uni_data) in enumerate(top, 1):
        print(f"{i}. {uni_data['name']} ({uni_data['country']})")
        print(f"   Mappable: {uni_data['mappable_count']}, "
              f"Spots: {uni_data['sem1_spots']}, "
              f"CGPA: {uni_data['min_cgpa']:.2f}")

    # Test country summary
    print("\n" + "="*80)
    print("\nCountry Summary:\n")
    summary = ranker.get_country_summary(filtered)
    for country in sorted(summary.keys()):
        stats = summary[country]
        print(f"{country}:")
        print(f"  Universities: {stats['count']}")
        print(f"  Total Sem 1 Spots: {stats['total_spots']}")
        print(f"  Avg Mappable Modules: {stats['avg_mappable']:.1f}")
        print(f"  Avg Min CGPA: {stats['avg_cgpa']:.2f}")
        print()

    # Test scoring
    print("="*80)
    print("\nScoring Test:\n")
    scored = ranker.calculate_scores(sample_data)
    scored_ranked = sorted(
        scored.items(),
        key=lambda x: -x[1]['score_breakdown']['total_score']
    )
    for i, (uni_id, uni_data) in enumerate(scored_ranked, 1):
        scores = uni_data['score_breakdown']
        print(f"{i}. {uni_data['name']:40} | Total: {scores['total_score']:.1f}")
        print(f"   (Mappable: {scores['mappable_score']:.1f}, "
              f"Spots: {scores['spots_score']:.1f}, "
              f"CGPA: {scores['cgpa_score']:.1f})")
