#!/usr/bin/env python3
"""
Smart Home — Chat Tier Pack Verifier  (P9-04)

Validates that generated chat tier packs exist, are fresh, and match
the expected structure.

Usage:
    python verify_context_pack.py --chat          # Verify chat packs
    python verify_context_pack.py --chat --strict  # Fail on warnings too

Exit codes:
    0 — All checks pass
    1 — One or more checks failed
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent
TIERS_CONFIG = REPO_ROOT / "AI_CONTEXT" / "TIERS" / "chat_tiers.yml"


def load_config() -> dict:
    if not TIERS_CONFIG.exists():
        return {}
    with open(TIERS_CONFIG) as f:
        return yaml.safe_load(f)


class PackVerifier:
    """Verifies chat tier pack structure and freshness."""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)
        print(f"  ✗ ERROR: {msg}")

    def warn(self, msg: str):
        self.warnings.append(msg)
        print(f"  ⚠ WARN:  {msg}")

    def ok(self, msg: str):
        print(f"  ✓ {msg}")

    def verify(self) -> int:
        """Run all verification checks. Returns exit code."""
        config = load_config()
        if not config:
            self.error("Config file not found or empty: AI_CONTEXT/TIERS/chat_tiers.yml")
            return 1

        settings = config.get("settings", {})
        output_dir = REPO_ROOT / settings.get("output_dir", "AI_CONTEXT/GENERATED_CHAT")
        staleness_days = settings.get("staleness_days", 7)
        chars_per_token = settings.get("chars_per_token", 4)

        print(f"Verifying chat tier packs in {output_dir}")
        print()

        # Check 1: Output directory exists
        print("[1] Output directory")
        if output_dir.exists():
            self.ok(f"{output_dir} exists")
        else:
            self.error(f"{output_dir} does not exist — run: python generate_context_pack.py --chat")
            return 1

        # Check 2: Required files exist
        print("\n[2] Required files")
        required_files = [
            "CHAT_INDEX.md",
            "CHAT_T0_BOOT.md",
            "CHAT_T1_CORE.md",
            "CHAT_T2_BUILD.md",
            "CHAT_T3_DEEP.md",
        ]
        for fname in required_files:
            fpath = output_dir / fname
            if fpath.exists():
                size = fpath.stat().st_size
                self.ok(f"{fname} ({size:,} bytes)")
            else:
                self.error(f"{fname} missing")

        # Check 3: Manifest exists and is valid
        print("\n[3] Manifest")
        manifest_path = output_dir / "CHAT_PACK_MANIFEST.json"
        manifest = None
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                self.ok(f"Manifest loaded ({len(manifest.get('packs', {}))} packs)")
            except json.JSONDecodeError as e:
                self.error(f"Manifest JSON parse error: {e}")
        else:
            self.warn("CHAT_PACK_MANIFEST.json not found (optional but recommended)")

        # Check 4: Staleness
        print("\n[4] Staleness check")
        cutoff = datetime.now(timezone.utc) - timedelta(days=staleness_days)
        for fname in required_files:
            fpath = output_dir / fname
            if fpath.exists():
                mtime = datetime.fromtimestamp(fpath.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    self.warn(f"{fname} is stale (modified {mtime.strftime('%Y-%m-%d')}, "
                              f"threshold {staleness_days} days)")
                else:
                    self.ok(f"{fname} is fresh (modified {mtime.strftime('%Y-%m-%d')})")

        # Check 5: SHA-256 integrity (if manifest exists)
        if manifest and "packs" in manifest:
            print("\n[5] Integrity check")
            for pack_name, info in manifest["packs"].items():
                fpath = output_dir / f"{pack_name}.md"
                if fpath.exists():
                    actual_sha = hashlib.sha256(fpath.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
                    expected_sha = info.get("sha256", "")
                    if actual_sha == expected_sha:
                        self.ok(f"{pack_name} SHA-256 matches")
                    else:
                        self.warn(f"{pack_name} SHA-256 mismatch (file modified after generation?)")

        # Check 6: Token budgets
        print("\n[6] Token budget check")
        tiers = config.get("tiers", {})
        for tier_key, tier_def in tiers.items():
            name = tier_def.get("name", tier_key)
            fpath = output_dir / f"{name}.md"
            if fpath.exists():
                content = fpath.read_text(encoding="utf-8")
                tokens = len(content) // chars_per_token
                max_tokens = tier_def.get("max_tokens", float("inf"))
                if tokens > max_tokens:
                    self.error(f"{name}: {tokens} tokens exceeds max {max_tokens}")
                else:
                    self.ok(f"{name}: ~{tokens} tokens (max {max_tokens})")

        # Check 7: Source documents exist
        print("\n[7] Source document availability")
        all_sources = set()
        for tier_def in tiers.values():
            for source in tier_def.get("sources", []):
                all_sources.add(source["path"])

        for source_path in sorted(all_sources):
            fpath = REPO_ROOT / source_path
            if fpath.exists():
                self.ok(f"{source_path}")
            else:
                self.warn(f"{source_path} not found")

        # Summary
        print()
        print("=" * 50)
        total_checks = len(self.errors) + len(self.warnings)
        print(f"Errors: {len(self.errors)}, Warnings: {len(self.warnings)}")

        if self.errors:
            print("RESULT: FAIL")
            return 1
        elif self.warnings and self.strict:
            print("RESULT: FAIL (strict mode)")
            return 1
        else:
            print("RESULT: PASS")
            return 0


def main():
    parser = argparse.ArgumentParser(description="Verify Chat Tier Packs")
    parser.add_argument("--chat", action="store_true", required=True,
                        help="Verify chat tier packs")
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as errors")
    args = parser.parse_args()

    verifier = PackVerifier(strict=args.strict)
    return verifier.verify()


if __name__ == "__main__":
    sys.exit(main())
