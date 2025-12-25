"""
Data processing modules for university analysis.
"""

from .data_cleaner import (
    UniversityNameNormalizer,
    UniversityDataCleaner,
    clean_and_group_universities,
    normalize_mappings
)
from .matcher import (
    UniversityMatcher,
    combine_data_sources,
    get_statistics
)
from .ranker import (
    UniversityRanker,
    filter_and_rank,
    get_top_n,
    summarize_by_country
)
from .output_generator import (
    OutputGenerator,
    save_outputs
)

__all__ = [
    'UniversityNameNormalizer',
    'UniversityDataCleaner',
    'clean_and_group_universities',
    'normalize_mappings',
    'UniversityMatcher',
    'combine_data_sources',
    'get_statistics',
    'UniversityRanker',
    'filter_and_rank',
    'get_top_n',
    'summarize_by_country',
    'OutputGenerator',
    'save_outputs',
]
