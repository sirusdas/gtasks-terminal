"""
Space and sub-space extraction and serialization utilities.

Spaces and sub-spaces ("super-tags") provide a hierarchical classification above tags:
Format in task notes:
---{spaces}
{spa::space_name:(sub::subspace_name1,sub::subspace_name2)}
"""

import re
from typing import Dict, List, Tuple


# Regex pattern to locate the ---{spaces} section
_SPACES_DIVIDER_REGEX = re.compile(
    r'(?:^|\r?\n)[ \t]*---[ \t]*\{spaces\}[ \t]*(?:\r?\n)([\s\S]*?)(?=(?:\r?\n[ \t]*---[ \t]*[^\r\n]*)|$)',
    re.IGNORECASE,
)

# Regex pattern for tags divider (--- followed by bracket tags)
_TAGS_DIVIDER_REGEX = re.compile(
    r'(?:^|\r?\n)[ \t]*---[ \t]*(?:\r?\n)((?:[ \t]*(?:\[[^\]\r\n]+\])[\s]*)+)(?=(?:\r?\n[ \t]*---[ \t]*[^\r\n]*)|$)',
    re.IGNORECASE,
)

# Regex pattern to match an individual space definition
# Examples: {spa::work:(sub::frontend,sub::backend)}, {spa::personal:()}, {spa::home}
_SPACE_ITEM_REGEX = re.compile(
    r'\{spa::([a-zA-Z0-9_\-\s]+?)(?::\(([^)]*)\))?\}',
    re.IGNORECASE,
)


def _is_valid_identifier(name: str) -> bool:
    """Validate a space or sub-space name."""
    if not name or not isinstance(name, str):
        return False
    t = name.strip()
    if not (1 <= len(t) <= 50):
        return False
    if any(c in t for c in '{}"\':,\r\n\t()'):
        return False
    return True


def extract_spaces_from_text(text: str) -> Dict[str, List[str]]:
    """
    Extract spaces and their sub-spaces from text notes.

    Args:
        text: Raw task notes text

    Returns:
        Dict mapping space name to list of sub-space names
        e.g. {'work': ['frontend', 'backend'], 'personal': []}
    """
    if not text:
        return {}

    spaces: Dict[str, List[str]] = {}

    # Check if text contains the explicit ---{spaces} section
    divider_match = _SPACES_DIVIDER_REGEX.search(text)
    search_chunk = divider_match.group(1) if divider_match else text

    for match in _SPACE_ITEM_REGEX.finditer(search_chunk):
        space_name = match.group(1).strip()
        if not _is_valid_identifier(space_name):
            continue

        raw_subspaces = match.group(2) or ''
        subspaces: List[str] = []

        if raw_subspaces.strip():
            for item in raw_subspaces.split(','):
                sub = item.strip()
                # Remove optional sub:: prefix
                if sub.lower().startswith('sub::'):
                    sub = sub[5:].strip()
                if sub and _is_valid_identifier(sub) and sub not in subspaces:
                    subspaces.append(sub)

        # Merge or add space
        if space_name in spaces:
            for s in subspaces:
                if s not in spaces[space_name]:
                    spaces[space_name].append(s)
        else:
            spaces[space_name] = subspaces

    return spaces


def split_notes_and_metadata(raw_text: str) -> Tuple[str, List[str], Dict[str, List[str]]]:
    """
    Splits raw task notes into:
      1. clean_notes (stripped of all dividers and metadata blocks)
      2. tags (extracted bracket tags)
      3. spaces (dict of space -> list of sub-spaces)

    Args:
        raw_text: Raw notes string from Google Tasks / local storage

    Returns:
        Tuple of (clean_notes, tags, spaces)
    """
    if not raw_text:
        return ('', [], {})

    from gtasks_cli.utils.tag_extractor import extract_tags_from_text

    text = str(raw_text)
    spaces = extract_spaces_from_text(text)

    # Extract tags from any tag divider block or bracket tags
    tags: List[str] = []
    tag_match = _TAGS_DIVIDER_REGEX.search(text)
    if tag_match:
        tags = extract_tags_from_text(tag_match.group(1))
    else:
        # Fallback to general bracket tags
        tags = extract_tags_from_text(text)

    # Strip the ---{spaces} section
    clean = _SPACES_DIVIDER_REGEX.sub('', text)

    # Strip the --- tag section
    clean = _TAGS_DIVIDER_REGEX.sub('', clean)

    # Also clean any leftover pure divider line or trailing whitespace
    clean = re.sub(r'(?:^|\r?\n)[ \t]*---[ \t]*(?:\{spaces\})?[ \t]*$', '', clean, flags=re.MULTILINE)
    clean = clean.strip()

    return (clean, tags, spaces)


def combine_notes_and_metadata(
    clean_notes: str,
    tags: List[str] = None,
    spaces: Dict[str, List[str]] = None,
) -> str:
    """
    Combines user clean notes, tags, and spaces into the canonical task notes format.

    Format:
    <clean_notes>

    ---
    [tag1][tag2]

    ---{spaces}
    {spa::space1:(sub::sub1,sub::sub2)}
    {spa::space2}

    Args:
        clean_notes: The user-facing notes text
        tags: List of tag strings
        spaces: Dict of space -> list of sub-spaces

    Returns:
        Formatted notes string
    """
    from gtasks_cli.utils.tag_extractor import _is_valid_tag

    clean = (clean_notes or '').strip()
    sections = []

    if clean:
        sections.append(clean)

    # Tags section
    if tags:
        clean_tags = []
        for t in tags:
            tag_str = str(t).strip().lstrip('[#').rstrip(']')
            if tag_str and _is_valid_tag(tag_str) and tag_str not in clean_tags:
                clean_tags.append(tag_str)

        if clean_tags:
            tags_line = ''.join(f'[{t}]' for t in clean_tags)
            sections.append(f'---\n{tags_line}')

    # Spaces section
    if spaces:
        space_lines = []
        for space_name, subspaces in spaces.items():
            spa = str(space_name).strip()
            if not _is_valid_identifier(spa):
                continue

            valid_subs = [
                str(s).strip()[5:].strip() if str(s).strip().lower().startswith('sub::') else str(s).strip()
                for s in subspaces
                if _is_valid_identifier(str(s).strip())
            ]
            valid_subs = list(dict.fromkeys(valid_subs))  # deduplicate preserving order

            if valid_subs:
                subs_formatted = ','.join(f'sub::{s}' for s in valid_subs)
                space_lines.append(f'{{spa::{spa}:({subs_formatted})}}')
            else:
                space_lines.append(f'{{spa::{spa}}}')

        if space_lines:
            spaces_block = '\n'.join(space_lines)
            sections.append(f'---{{spaces}}\n{spaces_block}')

    return '\n\n'.join(sections).strip()
