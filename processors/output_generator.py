"""
Output generation utilities for CSV and Markdown reports.
"""

import csv
import os
from datetime import datetime
from typing import Dict, List, Tuple
from processors.matcher import UniversityMatcher
from processors.ranker import UniversityRanker


class OutputGenerator:
    """Generate CSV and Markdown reports from university data."""

    def __init__(self, target_modules: List[str]):
        """
        Initialize output generator.

        Args:
            target_modules: List of target module codes
        """
        self.target_modules = target_modules
        self.matcher = UniversityMatcher()
        self.ranker = UniversityRanker()

    def generate_csv(self, ranked_data: List[Tuple[str, Dict]], output_path: str) -> None:
        """
        Generate CSV file with university analysis.

        Args:
            ranked_data: List of (uni_id, uni_data) tuples
            output_path: Path to save CSV file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Define CSV columns
        columns = [
            'Rank',
            'University Name',
            'Country',
            'University Code',
            'Sem 1 Spots',
            'Min CGPA',
            'Mappable Modules Count',
            'Coverage Score (%)',
        ]

        # Add columns for each target module
        for module in self.target_modules:
            columns.append(f'{module} Mapping')

        columns.extend([
            'Unmappable Modules',
            'Remarks'
        ])

        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()

            for rank, (uni_id, uni_data) in enumerate(ranked_data, 1):
                row = {
                    'Rank': rank,
                    'University Name': uni_data['name'],
                    'Country': uni_data['country'],
                    'University Code': uni_data.get('university_code', ''),
                    'Sem 1 Spots': uni_data['sem1_spots'],
                    'Min CGPA': uni_data['min_cgpa'],
                    'Mappable Modules Count': uni_data['mappable_count'],
                    'Coverage Score (%)': f"{uni_data['coverage_score']:.1f}",
                }

                # Add mapping for each module
                for module in self.target_modules:
                    mappings = uni_data['mappable_modules'].get(module, [])
                    row[f'{module} Mapping'] = self.matcher.get_mapping_summary(mappings)

                # Add unmappable modules
                row['Unmappable Modules'] = ', '.join(uni_data['unmappable_modules'])
                row['Remarks'] = uni_data.get('remarks', '')

                writer.writerow(row)

        print(f"✓ CSV saved to: {output_path}")

    def generate_markdown(self, ranked_data: List[Tuple[str, Dict]],
                         output_path: str, config: Dict = None) -> None:
        """
        Generate Markdown report with detailed analysis.

        Args:
            ranked_data: List of (uni_id, uni_data) tuples
            output_path: Path to save Markdown file
            config: Optional configuration dictionary
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Convert ranked data back to dict for statistics
        data_dict = dict(ranked_data)

        # Calculate statistics
        stats = self.ranker.get_country_summary(data_dict)
        grouped = self.ranker.group_by_country(ranked_data)
        top_15 = ranked_data[:15]  # Already ranked

        # Build markdown content
        lines = []

        # Header
        lines.append("# Exchange Universities Analysis Report")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---\n")

        # Summary Statistics
        lines.append("## Summary Statistics\n")
        lines.append(f"- **Total universities found:** {len(ranked_data)}")
        lines.append(f"- **Countries represented:** {len(stats)}")

        total_mappable = sum(uni['mappable_count'] for _, uni in ranked_data)
        avg_mappable = total_mappable / len(ranked_data) if ranked_data else 0
        lines.append(f"- **Average mappable modules:** {avg_mappable:.1f}")

        if ranked_data:
            top_coverage = max(uni['coverage_score'] for _, uni in ranked_data)
            lines.append(f"- **Top coverage score:** {top_coverage:.1f}%")

        # Target modules
        if config and 'target_modules' in config:
            lines.append(f"\n### Target Modules\n")
            for module in config['target_modules']:
                lines.append(f"- {module}")

        # Breakdown by Country
        lines.append("\n### Breakdown by Country\n")
        lines.append("| Country | Universities | Total Spots | Avg Mappable Modules | Avg Min CGPA |")
        lines.append("|---------|--------------|-------------|----------------------|--------------|")

        for country in sorted(stats.keys()):
            country_stats = stats[country]
            lines.append(
                f"| {country} | {country_stats['count']} | "
                f"{country_stats['total_spots']} | "
                f"{country_stats['avg_mappable']:.1f} | "
                f"{country_stats['avg_cgpa']:.2f} |"
            )

        # Top 15 Universities Overall
        lines.append("\n## Top 15 Universities Overall\n")
        lines.append("| Rank | University | Country | Mappable | Spots | Min CGPA |")
        lines.append("|------|------------|---------|----------|-------|----------|")

        for rank, (uni_id, uni_data) in enumerate(top_15, 1):
            lines.append(
                f"| {rank} | {uni_data['name']} | {uni_data['country']} | "
                f"{uni_data['mappable_count']}/6 | {uni_data['sem1_spots']} | "
                f"{uni_data['min_cgpa']:.2f} |"
            )

        # Detailed Results by Country
        lines.append("\n---\n")
        lines.append("## Detailed Results\n")

        for country in sorted(grouped.keys()):
            universities = grouped[country]

            lines.append(f"\n### {country}\n")

            for uni_id, uni_data in universities:
                lines.append(f"\n#### {uni_data['name']}\n")
                lines.append(f"- **University Code:** {uni_data.get('university_code', 'N/A')}")
                lines.append(f"- **Sem 1 Spots:** {uni_data['sem1_spots']}")
                lines.append(f"- **Min CGPA:** {uni_data['min_cgpa']:.2f}")
                lines.append(f"- **Mappable Modules:** {uni_data['mappable_count']}/6 ({uni_data['coverage_score']:.1f}%)")

                # Module mappings
                if uni_data['mappable_modules']:
                    lines.append(f"\n**Can Map:**\n")
                    for module, mappings in sorted(uni_data['mappable_modules'].items()):
                        details = self.matcher.get_detailed_mapping_info(mappings)
                        for detail in details:
                            lines.append(f"- ✅ {module} → {detail}")

                # Unmappable modules
                if uni_data['unmappable_modules']:
                    lines.append(f"\n**Cannot Map:**\n")
                    for module in sorted(uni_data['unmappable_modules']):
                        lines.append(f"- ❌ {module} (No approved mapping found)")

                # Remarks
                if uni_data.get('remarks'):
                    lines.append(f"\n**Remarks:** {uni_data['remarks']}")

                lines.append("\n---")

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"✓ Markdown report saved to: {output_path}")

    def generate_summary_text(self, ranked_data: List[Tuple[str, Dict]]) -> str:
        """
        Generate a brief text summary for console output.

        Args:
            ranked_data: List of (uni_id, uni_data) tuples

        Returns:
            Summary text
        """
        if not ranked_data:
            return "No universities found matching criteria."

        data_dict = dict(ranked_data)
        stats = self.ranker.get_country_summary(data_dict)

        lines = []
        lines.append(f"\n{'='*80}")
        lines.append("SUMMARY")
        lines.append(f"{'='*80}\n")
        lines.append(f"Total universities: {len(ranked_data)}")
        lines.append(f"Countries: {len(stats)}\n")

        # Top 5 universities
        lines.append("Top 5 Universities:\n")
        for rank, (uni_id, uni_data) in enumerate(ranked_data[:5], 1):
            lines.append(
                f"{rank}. {uni_data['name']} ({uni_data['country']}) - "
                f"{uni_data['mappable_count']}/6 modules, "
                f"{uni_data['sem1_spots']} spots, "
                f"CGPA {uni_data['min_cgpa']:.2f}"
            )

        lines.append(f"\n{'='*80}\n")

        return '\n'.join(lines)


def save_outputs(ranked_data: List[Tuple[str, Dict]],
                csv_path: str, markdown_path: str,
                config: Dict = None) -> None:
    """
    Main function to generate all outputs.

    Args:
        ranked_data: Ranked university data
        csv_path: Path for CSV output
        markdown_path: Path for Markdown output
        config: Optional configuration dictionary
    """
    # Get target modules from config or use defaults
    target_modules = config.get('target_modules', [
        'SC4001', 'SC4002', 'SC4062', 'SC4021', 'SC4023', 'SC4003'
    ]) if config else ['SC4001', 'SC4002', 'SC4062', 'SC4021', 'SC4023', 'SC4003']

    generator = OutputGenerator(target_modules)

    # Generate CSV
    generator.generate_csv(ranked_data, csv_path)

    # Generate Markdown
    generator.generate_markdown(ranked_data, markdown_path, config)

    # Print summary
    summary = generator.generate_summary_text(ranked_data)
    print(summary)


if __name__ == "__main__":
    # Test output generation
    print("Testing Output Generator\n")
    print("="*80)

    # Sample ranked data
    sample_data = [
        ("AU-MELB", {
            "name": "University of Melbourne",
            "country": "Australia",
            "university_code": "AU-MELB",
            "sem1_spots": 2,
            "min_cgpa": 3.7,
            "mappable_count": 5,
            "coverage_score": 83.3,
            "mappable_modules": {
                "SC4001": [{
                    "partner_module_code": "COMP30027",
                    "partner_module_name": "Machine Learning",
                    "approval_year": "2024"
                }],
                "SC4002": [{
                    "partner_module_code": "COMP90042",
                    "partner_module_name": "Natural Language Processing",
                    "approval_year": "2024"
                }],
                "SC4021": [],
                "SC4023": [],
                "SC4003": []
            },
            "unmappable_modules": ["SC4062"],
            "remarks": "Group of Eight member"
        }),
        ("DK-DTU", {
            "name": "Technical University of Denmark",
            "country": "Denmark",
            "university_code": "DK-DTU",
            "sem1_spots": 2,
            "min_cgpa": 3.6,
            "mappable_count": 3,
            "coverage_score": 50.0,
            "mappable_modules": {
                "SC4001": [{
                    "partner_module_code": "02456",
                    "partner_module_name": "Deep Learning",
                    "approval_year": "2024"
                }],
                "SC4002": [],
                "SC4021": [],
                "SC4023": [],
                "SC4003": []
            },
            "unmappable_modules": ["SC4002", "SC4062", "SC4021"],
            "remarks": ""
        })
    ]

    # Test configuration
    test_config = {
        'target_modules': ['SC4001', 'SC4002', 'SC4062', 'SC4021', 'SC4023', 'SC4003']
    }

    # Generate outputs to test directory
    test_csv = "test_outputs/test_analysis.csv"
    test_md = "test_outputs/test_report.md"

    save_outputs(sample_data, test_csv, test_md, test_config)

    print("\n✓ Test outputs generated successfully!")
