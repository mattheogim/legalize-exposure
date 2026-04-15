"""Mapping validation — compare mapper predictions against ground truth.

Runs the exposure mapper on each regulation in validation_100.json and
computes precision, recall, and F1 for both industry and ETF predictions.

Usage:
    python -m exposure.validation
    python -m exposure.validation --ground-truth validation_100.json --verbose
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from exposure.mapper import ExposureMapper
from exposure.fr_connector import FRExposureConnector


@dataclass
class ValidationResult:
    """Result for a single regulation."""
    document_number: str
    title: str
    agency: str

    # Ground truth
    actual_industries: set[str]
    actual_etfs: set[str]

    # Predicted
    predicted_industries: set[str]
    predicted_etfs: set[str]

    # Metrics
    industry_precision: float = 0.0
    industry_recall: float = 0.0
    industry_f1: float = 0.0
    etf_precision: float = 0.0
    etf_recall: float = 0.0
    etf_f1: float = 0.0

    # Errors
    industry_false_positives: set[str] = field(default_factory=set)
    industry_false_negatives: set[str] = field(default_factory=set)
    etf_false_positives: set[str] = field(default_factory=set)
    etf_false_negatives: set[str] = field(default_factory=set)

    # Mapping failure
    mapping_failed: bool = False
    error_message: str = ""


def _precision_recall_f1(predicted: set, actual: set) -> tuple[float, float, float]:
    """Compute precision, recall, F1 for two sets."""
    if not predicted and not actual:
        return 1.0, 1.0, 1.0
    if not predicted:
        return 0.0, 0.0, 0.0
    if not actual:
        return 0.0, 0.0, 0.0

    tp = len(predicted & actual)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(actual) if actual else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


def validate_single(entry: dict, connector: FRExposureConnector) -> ValidationResult:
    """Validate a single regulation against ground truth."""
    result = ValidationResult(
        document_number=entry["document_number"],
        title=entry["title"][:80],
        agency=entry["agency"],
        actual_industries=set(entry.get("industries", [])),
        actual_etfs=set(entry.get("etfs", [])),
        predicted_industries=set(),
        predicted_etfs=set(),
    )

    # Build a fake FR API response dict to feed the mapper.
    api_doc = {
        "document_number": entry["document_number"],
        "type": entry.get("doc_type", "Rule").upper().replace(" ", ""),
        "title": entry["title"],
        "abstract": "",
        "agency_names": [_agency_slug_to_name(entry["agency"])],
        "publication_date": entry.get("publication_date", ""),
        "effective_on": None,
        "comments_close_on": None,
        "docket_ids": [],
        "cfr_references": [],
        "html_url": entry.get("html_url", ""),
        "pdf_url": "",
        "significant": entry.get("significant", False),
        "action": "",
    }

    try:
        pipeline_result = connector.map_from_api_json(api_doc)

        if pipeline_result is None:
            result.mapping_failed = True
            result.error_message = "Mapper returned None"
        else:
            # Extract predicted industries (NAICS codes).
            for ind in pipeline_result.mapping.industries:
                result.predicted_industries.add(str(ind.naics_code)[:3])

            # Extract predicted ETFs.
            for etf in pipeline_result.mapping.etfs:
                result.predicted_etfs.add(etf.ticker)

    except Exception as e:
        result.mapping_failed = True
        result.error_message = str(e)

    # Compute metrics (use 3-digit NAICS prefix for industry comparison).
    actual_ind_3 = {code[:3] for code in result.actual_industries}
    pred_ind_3 = {code[:3] for code in result.predicted_industries}

    result.industry_precision, result.industry_recall, result.industry_f1 = \
        _precision_recall_f1(pred_ind_3, actual_ind_3)

    result.etf_precision, result.etf_recall, result.etf_f1 = \
        _precision_recall_f1(result.predicted_etfs, result.actual_etfs)

    # Error analysis.
    result.industry_false_positives = pred_ind_3 - actual_ind_3
    result.industry_false_negatives = actual_ind_3 - pred_ind_3
    result.etf_false_positives = result.predicted_etfs - result.actual_etfs
    result.etf_false_negatives = result.actual_etfs - result.predicted_etfs

    return result


def validate_all(ground_truth_path: str | Path, verbose: bool = False) -> list[ValidationResult]:
    """Run validation on all entries in ground truth file."""
    data = json.loads(Path(ground_truth_path).read_text())
    connector = FRExposureConnector()
    results: list[ValidationResult] = []

    for i, entry in enumerate(data):
        result = validate_single(entry, connector)
        results.append(result)

        if verbose:
            status = "FAIL" if result.mapping_failed else "OK"
            print(
                f"[{i+1:3d}/{len(data)}] {status} "
                f"IndF1={result.industry_f1:.2f} "
                f"EtfF1={result.etf_f1:.2f} "
                f"| {result.document_number} | {result.title[:50]}"
            )

    return results


def generate_report(results: list[ValidationResult]) -> str:
    """Generate a Markdown validation report."""
    lines: list[str] = []

    # Aggregate metrics.
    valid = [r for r in results if not r.mapping_failed]
    failed = [r for r in results if r.mapping_failed]

    avg_ind_p = sum(r.industry_precision for r in valid) / len(valid) if valid else 0
    avg_ind_r = sum(r.industry_recall for r in valid) / len(valid) if valid else 0
    avg_ind_f1 = sum(r.industry_f1 for r in valid) / len(valid) if valid else 0
    avg_etf_p = sum(r.etf_precision for r in valid) / len(valid) if valid else 0
    avg_etf_r = sum(r.etf_recall for r in valid) / len(valid) if valid else 0
    avg_etf_f1 = sum(r.etf_f1 for r in valid) / len(valid) if valid else 0

    lines.append("# Mapping Validation Report")
    lines.append(f"\nTotal: {len(results)} | Mapped: {len(valid)} | Failed: {len(failed)}")
    lines.append("")
    lines.append("## Aggregate Metrics")
    lines.append("")
    lines.append("| Metric | Industry (NAICS 3-digit) | ETF |")
    lines.append("|--------|:---:|:---:|")
    lines.append(f"| Precision | {avg_ind_p:.3f} | {avg_etf_p:.3f} |")
    lines.append(f"| Recall | {avg_ind_r:.3f} | {avg_etf_r:.3f} |")
    lines.append(f"| **F1** | **{avg_ind_f1:.3f}** | **{avg_etf_f1:.3f}** |")
    lines.append("")

    # Thresholds.
    ind_ok = "PASS" if avg_ind_f1 >= 0.7 else "FAIL"
    etf_ok = "PASS" if avg_etf_f1 >= 0.6 else "FAIL"
    lines.append(f"Industry F1 target (>0.7): **{ind_ok}** ({avg_ind_f1:.3f})")
    lines.append(f"ETF F1 target (>0.6): **{etf_ok}** ({avg_etf_f1:.3f})")
    lines.append("")

    # Error analysis.
    all_ind_fp: dict[str, int] = {}
    all_ind_fn: dict[str, int] = {}
    all_etf_fp: dict[str, int] = {}
    all_etf_fn: dict[str, int] = {}

    for r in valid:
        for code in r.industry_false_positives:
            all_ind_fp[code] = all_ind_fp.get(code, 0) + 1
        for code in r.industry_false_negatives:
            all_ind_fn[code] = all_ind_fn.get(code, 0) + 1
        for ticker in r.etf_false_positives:
            all_etf_fp[ticker] = all_etf_fp.get(ticker, 0) + 1
        for ticker in r.etf_false_negatives:
            all_etf_fn[ticker] = all_etf_fn.get(ticker, 0) + 1

    lines.append("## Top Industry False Positives (predicted but not in ground truth)")
    lines.append("")
    for code, count in sorted(all_ind_fp.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"- NAICS {code}: {count} times")
    lines.append("")

    lines.append("## Top Industry False Negatives (in ground truth but not predicted)")
    lines.append("")
    for code, count in sorted(all_ind_fn.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"- NAICS {code}: {count} times")
    lines.append("")

    lines.append("## Top ETF False Positives")
    lines.append("")
    for ticker, count in sorted(all_etf_fp.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"- {ticker}: {count} times")
    lines.append("")

    lines.append("## Top ETF False Negatives")
    lines.append("")
    for ticker, count in sorted(all_etf_fn.items(), key=lambda x: -x[1])[:10]:
        lines.append(f"- {ticker}: {count} times")
    lines.append("")

    if failed:
        lines.append("## Mapping Failures")
        lines.append("")
        for r in failed:
            lines.append(f"- {r.document_number}: {r.error_message}")
        lines.append("")

    return "\n".join(lines)


def _agency_slug_to_name(slug: str) -> str:
    """Convert agency slug to display name for FR API format."""
    return slug.replace("-", " ").title()


def main():
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    gt_path = "validation_100.json"

    for arg in sys.argv[1:]:
        if not arg.startswith("-") and arg.endswith(".json"):
            gt_path = arg

    print(f"Running validation against {gt_path}...")
    results = validate_all(gt_path, verbose=verbose)
    report = generate_report(results)
    print(report)

    # Save report.
    report_path = Path("validation_report.md")
    report_path.write_text(report)
    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    main()
