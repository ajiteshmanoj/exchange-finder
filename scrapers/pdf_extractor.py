"""
PDF extractor for NTU GEM Explorer Exchange Vacancy List.
Parses the PDF table and extracts university information.
"""

import pdfplumber
import pandas as pd
import re
from typing import Dict, List
import warnings

warnings.filterwarnings('ignore')


class PDFExtractor:
    """Extract university data from GEM Explorer PDF."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_universities_from_pdf(self) -> pd.DataFrame:
        """
        Extract all universities from the vacancy PDF.

        Returns:
            DataFrame with university information
        """
        print(f"  Reading PDF: {self.pdf_path}")

        all_rows = []

        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"  Processing {total_pages} pages...")

            for page_num, page in enumerate(pdf.pages, 1):
                # Extract tables from the page
                tables = page.extract_tables()

                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Process rows (skip header)
                    for row in table[1:]:  # Skip header row
                        if len(row) >= 8:  # Ensure row has enough columns
                            parsed_row = self._parse_row(row)
                            if parsed_row:
                                all_rows.append(parsed_row)

                if page_num % 5 == 0:
                    print(f"    Processed {page_num}/{total_pages} pages...")

        print(f"  ✓ Extracted {len(all_rows)} university entries from PDF")

        # Convert to DataFrame
        df = pd.DataFrame(all_rows)
        return df

    def _parse_row(self, row: List[str]) -> Dict:
        """
        Parse a single row from the PDF table.

        Expected columns:
        0: Continent
        1: Country/Region
        2: University Code
        3: University Sub Code
        4: University Name
        5: Status
        6: For (colleges)
        7: Full Year spots
        8: Sem 1 spots
        9: Sem 2 spots
        10: Min CGPA
        11: Remarks
        """
        try:
            # Clean and extract values
            continent = str(row[0] or "").strip()
            country = str(row[1] or "").strip()
            university_code = str(row[2] or "").strip()
            university_sub_code = str(row[3] or "").strip()
            university_name = str(row[4] or "").strip()
            status = str(row[5] or "").strip()
            status_for = str(row[6] or "").strip()
            full_year_spots = self._parse_number(row[7])
            sem1_spots = self._parse_number(row[8])
            sem2_spots = self._parse_number(row[9])
            min_cgpa = self._parse_float(row[10])
            remarks = str(row[11] or "").strip() if len(row) > 11 else ""

            # Skip if university name is empty or looks like a header
            if not university_name or university_name in ["University", "University Name"]:
                return None

            # Skip if country is empty
            if not country:
                return None

            return {
                'continent': continent,
                'country': country,
                'university_code': university_code,
                'university_sub_code': university_sub_code,
                'university_name': university_name,
                'status': status,
                'status_for': status_for,
                'full_year_spots': full_year_spots,
                'sem1_spots': sem1_spots,
                'sem2_spots': sem2_spots,
                'min_cgpa': min_cgpa,
                'remarks': remarks
            }

        except Exception as e:
            # Skip rows that can't be parsed
            return None

    def _parse_number(self, value) -> int:
        """Parse a number from string, return 0 if invalid."""
        if value is None:
            return 0
        try:
            value_str = str(value).strip()
            # Remove any non-numeric characters except numbers
            value_str = re.sub(r'[^\d]', '', value_str)
            return int(value_str) if value_str else 0
        except:
            return 0

    def _parse_float(self, value) -> float:
        """Parse a float from string, return 0.0 if invalid."""
        if value is None:
            return 0.0
        try:
            value_str = str(value).strip()
            # Keep decimal point
            value_str = re.sub(r'[^\d.]', '', value_str)
            return float(value_str) if value_str else 0.0
        except:
            return 0.0

    def filter_target_universities(self, df: pd.DataFrame, config: Dict) -> Dict:
        """
        Filter universities by target countries, college acceptance, and sem1 availability.

        Args:
            df: DataFrame with all universities
            config: Configuration dictionary

        Returns:
            Dictionary of filtered universities with university_code as key
        """
        target_countries = config['target_countries']
        student_college = config['student_college']

        print(f"\n  Filtering universities...")
        print(f"    Initial count: {len(df)}")

        # Filter by target countries
        df_filtered = df[df['country'].isin(target_countries)].copy()
        print(f"    After country filter ({', '.join(target_countries)}): {len(df_filtered)}")

        # Filter by CCDS acceptance (check if 'CCDS' or 'All' is in status_for column)
        df_filtered = df_filtered[
            df_filtered['status_for'].str.contains(student_college, case=False, na=False) |
            df_filtered['status_for'].str.contains('All', case=False, na=False)
        ]
        print(f"    After {student_college} acceptance filter: {len(df_filtered)}")

        # Filter by sem1_spots > 0
        df_filtered = df_filtered[df_filtered['sem1_spots'] > 0]
        print(f"    After Sem 1 availability filter (spots > 0): {len(df_filtered)}")

        # Convert to dictionary with university_code as key
        universities = {}
        for _, row in df_filtered.iterrows():
            # Create unique key (combine code and subcode if subcode exists)
            if row['university_sub_code']:
                key = f"{row['university_code']}_{row['university_sub_code']}"
            else:
                key = row['university_code']

            universities[key] = {
                'name': row['university_name'],
                'country': row['country'],
                'university_code': row['university_code'],
                'university_sub_code': row['university_sub_code'],
                'sem1_spots': row['sem1_spots'],
                'min_cgpa': row['min_cgpa'],
                'accepts_ccds': True,
                'remarks': row['remarks']
            }

        print(f"  ✓ Final filtered count: {len(universities)} universities\n")

        # Show breakdown by country
        country_counts = df_filtered['country'].value_counts()
        print("  Breakdown by country:")
        for country, count in country_counts.items():
            print(f"    {country}: {count}")

        return universities


def extract_and_filter_universities(pdf_path: str, config: Dict) -> Dict:
    """
    Main function to extract and filter universities from PDF.

    Args:
        pdf_path: Path to PDF file
        config: Configuration dictionary

    Returns:
        Dictionary of filtered universities
    """
    extractor = PDFExtractor(pdf_path)
    df = extractor.extract_universities_from_pdf()
    universities = extractor.filter_target_universities(df, config)
    return universities


if __name__ == "__main__":
    # Test extraction
    import yaml

    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    pdf_path = "210125_GEM_Explorer_Vacancy_List_for_AY2526_Full_Year_Recruitment.pdf"
    universities = extract_and_filter_universities(pdf_path, config)

    print(f"\nTotal universities found: {len(universities)}")
    print("\nSample universities:")
    for i, (key, uni) in enumerate(list(universities.items())[:5]):
        print(f"\n{i+1}. {uni['name']} ({uni['country']})")
        print(f"   Code: {key}")
        print(f"   Sem 1 Spots: {uni['sem1_spots']}")
        print(f"   Min CGPA: {uni['min_cgpa']}")
