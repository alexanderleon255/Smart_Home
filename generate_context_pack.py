#!/usr/bin/env python3
"""
Smart Home — Chat Tier Pack Generator  (P9-03)

Reads AI_CONTEXT/TIERS/chat_tiers.yml and produces the 5 tier pack files
into AI_CONTEXT/GENERATED_CHAT/.

Usage:
    python generate_context_pack.py --chat          # Generate chat packs
    python generate_context_pack.py --chat --dry-run # Show what would be generated

Output:
    AI_CONTEXT/GENERATED_CHAT/CHAT_INDEX.md
    AI_CONTEXT/GENERATED_CHAT/CHAT_T0_BOOT.md
    AI_CONTEXT/GENERATED_CHAT/CHAT_T1_CORE.md
    AI_CONTEXT/GENERATED_CHAT/CHAT_T2_BUILD.md
    AI_CONTEXT/GENERATED_CHAT/CHAT_T3_DEEP.md
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent
TIERS_CONFIG = REPO_ROOT / "AI_CONTEXT" / "TIERS" / "chat_tiers.yml"


def load_config() -> dict:
    """Load and validate the tier configuration YAML."""
    if not TIERS_CONFIG.exists():
        print(f"ERROR: Config not found: {TIERS_CONFIG}", file=sys.stderr)
        sys.exit(1)
    with open(TIERS_CONFIG) as f:
        return yaml.safe_load(f)


def estimate_tokens(text: str, chars_per_token: int = 4) -> int:
    """Approximate token count from character count."""
    return len(text) // chars_per_token


def extract_section(content: str, section: str) -> str:
    """Extract a named section from a markdown document.

    Currently supported section names:
      - "locked_only": everything between '## Locked Decisions' and the next '## '
      - "executive_summary": everything between '## Executive Summary' and the next '## '
      - "full": return entire content
    """
    if section == "full":
        return content

    section_map = {
        "locked_only": r"## Locked Decisions.*?\n",
        "executive_summary": r"## Executive Summary\s*\n",
    }

    pattern = section_map.get(section)
    if not pattern:
        print(f"WARNING: Unknown section filter '{section}', using full content",
              file=sys.stderr)
        return content

    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        # Try a more lenient match
        print(f"WARNING: Section '{section}' not found in document, using full content",
              file=sys.stderr)
        return content

    start = match.start()
    # Find next ## heading (or end of file)
    next_heading = re.search(r"\n## ", content[match.end():])
    if next_heading:
        end = match.end() + next_heading.start()
    else:
        end = len(content)

    return content[start:end].strip()


def load_source(source: dict) -> str:
    """Load a source file and optionally extract a section."""
    path = REPO_ROOT / source["path"]
    if not path.exists():
        print(f"WARNING: Source not found: {path}", file=sys.stderr)
        return f"<!-- Source not found: {source['path']} -->\n"

    content = path.read_text(encoding="utf-8")

    # Strip markdown fenced code wrappers if the whole file is wrapped
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[-1].strip() == "```" or (len(lines) > 1 and lines[-1].strip() == "" and lines[-2].strip() == "```"):
            content = "\n".join(lines[1:])
            if content.rstrip().endswith("```"):
                content = content.rstrip()[:-3].rstrip()

    include_mode = source.get("include", "full")
    return extract_section(content, include_mode)


def build_tier_pack(tier_key: str, tier_def: dict, config: dict, timestamp: str) -> str:
    """Assemble a single tier pack from its definition."""
    parts = []

    # Header from shared config
    shared = config.get("shared", {})
    header = shared.get("header", "")
    if header:
        parts.append(header.replace("{timestamp}", timestamp))

    # Tier metadata
    parts.append(f"# {tier_def['name']}")
    parts.append(f"\n**Purpose:** {tier_def['purpose']}  ")
    parts.append(f"**Generated:** {timestamp}  ")
    parts.append(f"**Tier:** {tier_key}")
    parts.append("")

    # Inline sections (defined in YAML)
    for section in tier_def.get("sections", []):
        parts.append(f"## {section['name']}")
        parts.append("")
        parts.append(section["content"].rstrip())
        parts.append("")

    # Source documents
    sources = tier_def.get("sources", [])
    if sources:
        parts.append("---")
        parts.append("")

    for source in sources:
        source_content = load_source(source)
        if source_content:
            # Add source file header
            include_mode = source.get("include", "full")
            label = source["path"]
            if include_mode != "full":
                label += f" [{include_mode}]"
            parts.append(f"<!-- Source: {label} -->")
            parts.append("")
            parts.append(source_content)
            parts.append("")

    return "\n".join(parts)


def build_index(config: dict, manifest: dict, timestamp: str) -> str:
    """Build the CHAT_INDEX.md file."""
    index_def = config.get("index", {})
    content = index_def.get("content", "# Chat Tier Pack Index\n")

    # Append manifest
    parts = [content.rstrip(), "", "---", "", "## Pack Manifest", ""]
    parts.append("| Pack | Tokens | SHA-256 (first 12) | Generated |")
    parts.append("|------|--------|--------------------|-----------|")

    for name, info in manifest.items():
        sha_short = info["sha256"][:12]
        parts.append(f"| `{name}` | ~{info['tokens']} | `{sha_short}` | {timestamp} |")

    parts.append("")
    parts.append(f"\n*Generated: {timestamp}*")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Generate Chat Tier Packs")
    parser.add_argument("--chat", action="store_true", required=True,
                        help="Generate chat tier packs")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be generated without writing files")
    args = parser.parse_args()

    config = load_config()
    settings = config.get("settings", {})
    output_dir = REPO_ROOT / settings.get("output_dir", "AI_CONTEXT/GENERATED_CHAT")
    chars_per_token = settings.get("chars_per_token", 4)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    tiers = config.get("tiers", {})
    manifest = {}
    warnings = []

    print(f"Generating chat tier packs → {output_dir}")
    print(f"Timestamp: {timestamp}")
    print()

    for tier_key in ["t0_boot", "t1_core", "t2_build", "t3_deep"]:
        tier_def = tiers.get(tier_key)
        if not tier_def:
            print(f"WARNING: Tier '{tier_key}' not found in config", file=sys.stderr)
            continue

        name = tier_def["name"]
        content = build_tier_pack(tier_key, tier_def, config, timestamp)
        tokens = estimate_tokens(content, chars_per_token)
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

        target = tier_def.get("target_tokens", 0)
        max_tokens = tier_def.get("max_tokens", float("inf"))

        status = "OK"
        if tokens > max_tokens:
            status = f"OVER MAX ({tokens} > {max_tokens})"
            warnings.append(f"{name}: {tokens} tokens exceeds max {max_tokens}")
        elif target and tokens > target * 1.25:
            status = f"OVER TARGET ({tokens} > {target}*1.25)"
            warnings.append(f"{name}: {tokens} tokens exceeds target {target} by >25%")

        print(f"  {name}: {tokens:,} tokens, {len(content):,} chars — {status}")

        manifest[name] = {"tokens": tokens, "sha256": sha}

        if not args.dry_run:
            outfile = output_dir / f"{name}.md"
            outfile.write_text(content, encoding="utf-8")

    # Generate index
    index_content = build_index(config, manifest, timestamp)
    index_tokens = estimate_tokens(index_content, chars_per_token)
    print(f"  CHAT_INDEX: {index_tokens:,} tokens")

    if not args.dry_run:
        (output_dir / "CHAT_INDEX.md").write_text(index_content, encoding="utf-8")

    # Write manifest JSON
    manifest_data = {
        "generated": timestamp,
        "generator": "generate_context_pack.py --chat",
        "packs": manifest,
    }
    if not args.dry_run:
        (output_dir / "CHAT_PACK_MANIFEST.json").write_text(
            json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

    print()
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  ⚠ {w}")
        print()

    if args.dry_run:
        print("(dry-run mode — no files written)")
    else:
        print(f"Done. {len(manifest) + 1} files written to {output_dir}")
        print(f"Manifest: {output_dir / 'CHAT_PACK_MANIFEST.json'}")

    return 0 if not warnings else 0  # Warnings are non-fatal


if __name__ == "__main__":
    sys.exit(main())
