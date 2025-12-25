#!/usr/bin/env python3
"""
NTU Exchange University Scraper
Main orchestrator for the scraping and analysis pipeline.
Uses Selenium for browser-based SSO authentication and scraping.
"""

import os
import sys
import yaml
import argparse
from datetime import datetime

# Import modules
from utils.crypto import CredentialManager, setup_credentials
from scrapers.pdf_extractor import PDFExtractor
from scrapers.selenium_scraper import SeleniumNTUScraper
from processors.data_cleaner import clean_and_group_universities, normalize_mappings
from processors.matcher import combine_data_sources, get_statistics
from processors.ranker import filter_and_rank, summarize_by_country
from processors.output_generator import save_outputs


def print_banner():
    """Print application banner."""
    print("\n" + "="*80)
    print("NTU EXCHANGE UNIVERSITY SCRAPER")
    print("Find suitable exchange universities based on module mappings")
    print("Powered by Selenium WebDriver")
    print("="*80 + "\n")


def load_config(config_path: str = 'config/config.yaml') -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_path):
        print(f"❌ Error: Configuration file not found at {config_path}")
        sys.exit(1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


def setup_credentials_if_needed(credential_manager: CredentialManager) -> None:
    """
    Setup credentials if they don't exist.

    Args:
        credential_manager: CredentialManager instance
    """
    if not credential_manager.credentials_exist():
        print("\n⚠️  No credentials found. Let's set them up.\n")
        setup_credentials()
        print()


def extract_pdf_data(config: dict) -> dict:
    """
    Extract and filter university data from PDF.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary of filtered universities
    """
    print("\n" + "="*80)
    print("STEP 1/5: Extracting universities from PDF")
    print("="*80 + "\n")

    pdf_path = config['pdf_file']

    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found at {pdf_path}")
        sys.exit(1)

    # Extract from PDF
    extractor = PDFExtractor(pdf_path)
    df = extractor.extract_universities_from_pdf()

    # Filter by criteria
    filtered_unis = extractor.filter_target_universities(df, config)

    print(f"\n  ✓ Found {len(filtered_unis)} universities matching criteria")

    return filtered_unis


def scrape_mappings_selenium(credential_manager: CredentialManager,
                              universities: dict,
                              config: dict,
                              headless: bool = True) -> dict:
    """
    Scrape module mappings using Selenium browser automation.

    Args:
        credential_manager: CredentialManager instance
        universities: Dictionary of universities
        config: Configuration dictionary
        headless: Run browser in headless mode

    Returns:
        Dictionary of mapping data
    """
    print("\n" + "="*80)
    print("STEP 2/5: Logging in and scraping module mappings (Selenium)")
    print("="*80 + "\n")

    # Get credentials
    try:
        credentials = credential_manager.decrypt_credentials()
    except Exception as e:
        print(f"❌ Error: Failed to decrypt credentials: {e}")
        print("   Please run setup again to store credentials.")
        sys.exit(1)

    modules = config['target_modules']

    print(f"  Target modules: {', '.join(modules)}")
    print(f"  Universities to process: {len(universities)}")
    print(f"  Headless mode: {headless}")

    # Create and run Selenium scraper
    scraper = SeleniumNTUScraper(credentials, config, headless=headless)

    try:
        # Start browser
        if not scraper.start():
            print("❌ Failed to start browser")
            sys.exit(1)

        # Login
        if not scraper.login():
            print("❌ Login failed. Please check your credentials.")
            sys.exit(1)

        # Scrape all mappings
        mapping_data = scraper.scrape_all_mappings(universities, modules)

        return mapping_data

    finally:
        scraper.close()


def process_and_rank_data(universities: dict, mapping_data: dict, config: dict) -> list:
    """
    Process, clean, match, and rank university data.

    Args:
        universities: University data from PDF
        mapping_data: Module mapping data from scraper
        config: Configuration dictionary

    Returns:
        List of ranked universities
    """
    print("\n" + "="*80)
    print("STEP 3/5: Processing and ranking results")
    print("="*80 + "\n")

    # Clean and group universities
    print("  Cleaning and grouping university variations...")
    cleaned_unis = clean_and_group_universities(universities)

    # Normalize mapping data
    print("  Normalizing mapping data...")
    normalized_mappings = normalize_mappings(mapping_data)

    # Combine data sources
    print("  Matching universities with module mappings...")
    integrated_data = combine_data_sources(cleaned_unis, normalized_mappings)

    # Calculate statistics
    stats = get_statistics(integrated_data)
    print(f"\n  Statistics:")
    print(f"    Total universities: {stats['total_universities']}")
    print(f"    Average mappable modules: {stats['avg_mappable_modules']:.1f}")

    # Filter and rank
    min_mappable = config.get('min_mappable_modules', 2)
    print(f"\n  Filtering universities with minimum {min_mappable} mappable modules...")
    ranked_data = filter_and_rank(integrated_data, min_mappable=min_mappable)

    print(f"  ✓ {len(ranked_data)} universities meet criteria")

    return ranked_data


def generate_outputs(ranked_data: list, config: dict) -> None:
    """
    Generate CSV and Markdown reports.

    Args:
        ranked_data: Ranked university data
        config: Configuration dictionary
    """
    print("\n" + "="*80)
    print("STEP 4/5: Generating outputs")
    print("="*80 + "\n")

    csv_path = config['outputs']['csv']
    markdown_path = config['outputs']['markdown']

    save_outputs(ranked_data, csv_path, markdown_path, config)


def clear_checkpoint():
    """Clear checkpoint file for fresh start."""
    checkpoint_file = "checkpoint.json"
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print("✓ Checkpoint cleared - starting fresh")


def main(args):
    """Main execution function."""
    print_banner()

    # Load configuration
    config = load_config(args.config)

    # Setup credentials if needed
    credential_manager = CredentialManager()

    if args.setup:
        setup_credentials()
        print("\n✓ Credentials setup complete!")
        return

    if args.clear_checkpoint:
        clear_checkpoint()
        if not args.run:
            return

    setup_credentials_if_needed(credential_manager)

    try:
        # STEP 1: Extract PDF data
        universities = extract_pdf_data(config)

        # STEP 2: Scrape module mappings using Selenium
        mapping_data = scrape_mappings_selenium(
            credential_manager,
            universities,
            config,
            headless=not args.show_browser
        )

        # STEP 3: Process and rank
        ranked_data = process_and_rank_data(universities, mapping_data, config)

        # STEP 4: Generate outputs
        generate_outputs(ranked_data, config)

        # Final summary
        print("\n" + "="*80)
        print("✅ SCRAPING COMPLETE!")
        print("="*80 + "\n")
        print(f"Found {len(ranked_data)} suitable universities")
        print(f"\nOutputs saved:")
        print(f"  📊 CSV: {config['outputs']['csv']}")
        print(f"  📄 Markdown: {config['outputs']['markdown']}")
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Progress has been saved to checkpoint.")
        print("   Run again to resume from where you left off.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='NTU Exchange University Scraper - Find universities based on module mappings'
    )

    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )

    parser.add_argument(
        '--setup',
        action='store_true',
        help='Setup/update stored credentials'
    )

    parser.add_argument(
        '--show-browser',
        action='store_true',
        help='Show browser window instead of running headless (useful for debugging)'
    )

    parser.add_argument(
        '--clear-checkpoint',
        action='store_true',
        help='Clear checkpoint and start fresh'
    )

    parser.add_argument(
        '--run',
        action='store_true',
        help='Run scraper after clearing checkpoint (use with --clear-checkpoint)'
    )

    args = parser.parse_args()

    main(args)
