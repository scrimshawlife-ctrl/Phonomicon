#!/usr/bin/env python3
"""
Corpus ingestion and validation script.

ABX-Core: Validates corpus integrity, reducing data ambiguity.
SEED: Ensures all corpus records conform to schema.

Usage:
    python scripts/ingest_corpus.py [--validate-only] [--rebuild-index]
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from phonomicon.config import get_settings
from phonomicon.core.corpus_models import (
    AffectRecord,
    AudioFeaturesRecord,
    MetricsRecord,
    MintRecord,
    RarityCollectionRecord,
    SymbolicLinkRecord,
    UXSessionRecord,
    VisualMetaRecord,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class CorpusIngester:
    """
    Corpus ingestion and validation engine.

    ABX-Core: Centralized ingestion reduces corpus management complexity.
    """

    def __init__(self, corpus_root: Path):
        self.corpus_root = corpus_root
        self.stats = {
            "audio_features": {"valid": 0, "invalid": 0},
            "affect": {"valid": 0, "invalid": 0},
            "visual_meta": {"valid": 0, "invalid": 0},
            "symbolic_links": {"valid": 0, "invalid": 0},
            "rarity_collections": {"valid": 0, "invalid": 0},
            "mints": {"valid": 0, "invalid": 0},
            "ux_sessions": {"valid": 0, "invalid": 0},
            "metrics": {"valid": 0, "invalid": 0},
        }
        self.errors: list[dict[str, Any]] = []

    def ingest_all(self, validate_only: bool = False) -> bool:
        """
        Ingest and validate all corpus data.

        Args:
            validate_only: If True, only validate without building indices

        Returns:
            True if successful, False if errors occurred
        """
        logger.info(f"Starting corpus ingestion from {self.corpus_root}")

        # Ingest each corpus core
        success = True
        success &= self._ingest_audio_features()
        success &= self._ingest_affect_labels()
        success &= self._ingest_visual_meta()
        success &= self._ingest_symbolic_links()
        success &= self._ingest_rarity_collections()
        success &= self._ingest_mints()
        success &= self._ingest_ux_sessions()
        success &= self._ingest_metrics()

        # Print statistics
        self._print_stats()

        # Build indices if not validate-only
        if not validate_only and success:
            self._build_indices()

        return success

    def _ingest_audio_features(self) -> bool:
        """Ingest and validate AUDIO_CORE features."""
        logger.info("Ingesting audio features...")
        features_path = self.corpus_root / "audio" / "features"

        if not features_path.exists():
            logger.warning(f"Audio features directory not found: {features_path}")
            return True  # Not an error if corpus is empty

        for jsonl_file in features_path.glob("*.jsonl"):
            self._validate_jsonl(jsonl_file, AudioFeaturesRecord, "audio_features")

        return self.stats["audio_features"]["invalid"] == 0

    def _ingest_affect_labels(self) -> bool:
        """Ingest and validate AFFECT_CORE labels."""
        logger.info("Ingesting affect labels...")
        labels_file = self.corpus_root / "affect" / "labels.jsonl"

        if not labels_file.exists():
            logger.warning(f"Affect labels file not found: {labels_file}")
            return True

        self._validate_jsonl(labels_file, AffectRecord, "affect")
        return self.stats["affect"]["invalid"] == 0

    def _ingest_visual_meta(self) -> bool:
        """Ingest and validate VISUAL_CORE metadata."""
        logger.info("Ingesting visual metadata...")
        meta_file = self.corpus_root / "visual" / "meta" / "meta.jsonl"

        if not meta_file.exists():
            logger.warning(f"Visual metadata file not found: {meta_file}")
            return True

        self._validate_jsonl(meta_file, VisualMetaRecord, "visual_meta")
        return self.stats["visual_meta"]["invalid"] == 0

    def _ingest_symbolic_links(self) -> bool:
        """Ingest and validate SYMBOLIC_CORE links."""
        logger.info("Ingesting symbolic links...")
        links_file = self.corpus_root / "symbolic" / "links.jsonl"

        if not links_file.exists():
            logger.warning(f"Symbolic links file not found: {links_file}")
            return True

        self._validate_jsonl(links_file, SymbolicLinkRecord, "symbolic_links")
        return self.stats["symbolic_links"]["invalid"] == 0

    def _ingest_rarity_collections(self) -> bool:
        """Ingest and validate RARITY_CORE collections."""
        logger.info("Ingesting rarity collections...")
        collections_file = self.corpus_root / "rarity" / "collections.jsonl"

        if not collections_file.exists():
            logger.warning(f"Rarity collections file not found: {collections_file}")
            return True

        self._validate_jsonl(collections_file, RarityCollectionRecord, "rarity_collections")
        return self.stats["rarity_collections"]["invalid"] == 0

    def _ingest_mints(self) -> bool:
        """Ingest and validate PROVENANCE_CORE mints."""
        logger.info("Ingesting mint records...")
        mints_file = self.corpus_root / "provenance" / "mints.jsonl"

        if not mints_file.exists():
            logger.warning(f"Mint records file not found: {mints_file}")
            return True

        self._validate_jsonl(mints_file, MintRecord, "mints")
        return self.stats["mints"]["invalid"] == 0

    def _ingest_ux_sessions(self) -> bool:
        """Ingest and validate USER_FLOW_CORE sessions."""
        logger.info("Ingesting UX sessions...")
        sessions_file = self.corpus_root / "ux" / "sessions.jsonl"

        if not sessions_file.exists():
            logger.warning(f"UX sessions file not found: {sessions_file}")
            return True

        self._validate_jsonl(sessions_file, UXSessionRecord, "ux_sessions")
        return self.stats["ux_sessions"]["invalid"] == 0

    def _ingest_metrics(self) -> bool:
        """Ingest and validate METRICS_CORE metrics."""
        logger.info("Ingesting metrics...")
        metrics_file = self.corpus_root / "metrics" / "metrics.jsonl"

        if not metrics_file.exists():
            logger.warning(f"Metrics file not found: {metrics_file}")
            return True

        self._validate_jsonl(metrics_file, MetricsRecord, "metrics")
        return self.stats["metrics"]["invalid"] == 0

    def _validate_jsonl(self, file_path: Path, model_class: type, stat_key: str) -> None:
        """
        Validate a JSONL file against a Pydantic model.

        ABX-Core: Schema validation reduces data corruption risk.
        """
        try:
            with open(file_path, "r") as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        model_class.model_validate(data)
                        self.stats[stat_key]["valid"] += 1
                    except json.JSONDecodeError as e:
                        self.stats[stat_key]["invalid"] += 1
                        self.errors.append(
                            {
                                "file": str(file_path),
                                "line": line_num,
                                "error": f"JSON decode error: {e}",
                            }
                        )
                    except ValidationError as e:
                        self.stats[stat_key]["invalid"] += 1
                        self.errors.append(
                            {
                                "file": str(file_path),
                                "line": line_num,
                                "error": f"Validation error: {e}",
                            }
                        )
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")

    def _build_indices(self) -> None:
        """
        Build corpus indices for efficient lookup.

        ABX-Core: Indices reduce lookup time complexity.

        Note:
            TODO: Implement real index building.
            Should create:
            - audio_id -> features mapping
            - audio_id -> affect labels mapping
            - image_id -> metadata mapping
            - collection_id -> traits schema mapping
            - Possibly use SQLite or pickle for persistence
        """
        logger.info("Building corpus indices...")
        # Placeholder: Would build in-memory indices or persistent stores
        logger.info("Index building not yet implemented")

    def _print_stats(self) -> None:
        """Print ingestion statistics."""
        logger.info("\n" + "=" * 60)
        logger.info("CORPUS INGESTION STATISTICS")
        logger.info("=" * 60)

        for key, counts in self.stats.items():
            total = counts["valid"] + counts["invalid"]
            if total > 0:
                logger.info(f"{key:30} Valid: {counts['valid']:5} Invalid: {counts['invalid']:5}")

        if self.errors:
            logger.error(f"\n{len(self.errors)} validation errors occurred:")
            for error in self.errors[:10]:  # Show first 10 errors
                logger.error(f"  {error['file']}:{error['line']} - {error['error']}")
            if len(self.errors) > 10:
                logger.error(f"  ... and {len(self.errors) - 10} more errors")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Ingest and validate Phonomicon corpus")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate corpus without building indices",
    )
    parser.add_argument(
        "--rebuild-index", action="store_true", help="Force rebuild of corpus indices"
    )
    parser.add_argument(
        "--corpus-root", type=Path, help="Override corpus root path from config"
    )

    args = parser.parse_args()

    # Get corpus root
    settings = get_settings()
    corpus_root = args.corpus_root or settings.corpus_root

    if not corpus_root.exists():
        logger.error(f"Corpus root does not exist: {corpus_root}")
        logger.info("Please create corpus directory structure and populate with data")
        return 1

    # Run ingestion
    ingester = CorpusIngester(corpus_root)
    success = ingester.ingest_all(validate_only=args.validate_only)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
