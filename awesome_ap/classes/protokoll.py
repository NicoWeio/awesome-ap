from dataclasses import dataclass
from functools import cached_property

from ..analyze.analyze_code import analyze_dirs
from ..console import *
from .file import File
from .repo import Repo


@dataclass(order=True)
class Protokoll:
    dirs: list[File]
    pdfs: list[File]
    repo: Repo
    versuch: int

    def __repr__(self):
        return f'<Protokoll {self.repo.full_name} # {self.versuch}>'

    @cached_property
    def code_analysis(self):
        analysis_map = analyze_dirs([f.path for f in self.dirs])  # {filename: analysis}
        valid_analysis_results = [a for a in analysis_map.values() if a]

        return {
            # meta ↓
            'num_files': len(analysis_map),
            'has_errors': any(not a for a in analysis_map.values()),
            # cumlated ↓
            'total_lloc': sum(a.lloc for a in valid_analysis_results),
            'total_sloc': sum(a.sloc for a in valid_analysis_results),
            'total_comments': sum(a.comments for a in valid_analysis_results),
            'total_single_comments': sum(a.single_comments for a in valid_analysis_results),
            'total_comments_of_interest': sum(a.comments_of_interest for a in valid_analysis_results),
            # calculated ↓
            # NOTE: Derived metrics shall be calculated by the frontend/… (for now), so they don't need to be stored in the export.
            # 'comments_of_interest_per_lloc': total_comments_of_interest / total_lloc if total_lloc else None,
        }
