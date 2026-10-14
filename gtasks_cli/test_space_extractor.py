import sys
from gtasks_cli.utils.space_extractor import (
    extract_spaces_from_text,
    split_notes_and_metadata,
    combine_notes_and_metadata,
)


def test_extract_spaces_standard():
    notes = """Review architectural documents.

---
[work][urgent]

---{spaces}
{spa::engineering:(sub::frontend,sub::backend)}
{spa::personal:(sub::finance,sub::health)}
"""
    spaces = extract_spaces_from_text(notes)
    assert spaces == {
        'engineering': ['frontend', 'backend'],
        'personal': ['finance', 'health'],
    }


def test_extract_spaces_without_subspaces():
    # Case: empty parentheses or no colon
    notes1 = """---{spaces}
{spa::work}
{spa::personal:()}
"""
    assert extract_spaces_from_text(notes1) == {
        'work': [],
        'personal': [],
    }


def test_extract_spaces_single_line_multiple():
    # Case: multiple spaces on the same line
    notes = "---{spaces}\n{spa::engineering:(sub::dev)} {spa::ops:(sub::ci,sub::cd)}"
    spaces = extract_spaces_from_text(notes)
    assert spaces == {
        'engineering': ['dev'],
        'ops': ['ci', 'cd'],
    }


def test_extract_spaces_whitespace_and_casing():
    notes = """---{spaces}
{spa::  my-project  :( sub::sub_1 , sub::sub-2 )}
"""
    spaces = extract_spaces_from_text(notes)
    assert spaces == {
        'my-project': ['sub_1', 'sub-2'],
    }


def test_split_notes_and_metadata():
    raw = """Important client meeting notes here.
Second line of notes.

---
[client][p0]

---{spaces}
{spa::consulting:(sub::client_a)}
"""
    clean_notes, tags, spaces = split_notes_and_metadata(raw)
    assert clean_notes == "Important client meeting notes here.\nSecond line of notes."
    assert tags == ['client', 'p0']
    assert spaces == {'consulting': ['client_a']}


def test_split_notes_only_spaces():
    raw = """Clean description only.

---{spaces}
{spa::work:(sub::backend)}
"""
    clean_notes, tags, spaces = split_notes_and_metadata(raw)
    assert clean_notes == "Clean description only."
    assert tags == []
    assert spaces == {'work': ['backend']}


def test_split_notes_only_tags():
    raw = """Regular note.

---
[tag1][tag2]
"""
    clean_notes, tags, spaces = split_notes_and_metadata(raw)
    assert clean_notes == "Regular note."
    assert tags == ['tag1', 'tag2']
    assert spaces == {}


def test_combine_notes_and_metadata_roundtrip():
    clean = "Ship the feature release"
    tags = ['release', 'v2']
    spaces = {'core': ['engine', 'db'], 'sidecar': []}

    combined = combine_notes_and_metadata(clean, tags, spaces)
    expected = """Ship the feature release

---
[release][v2]

---{spaces}
{spa::core:(sub::engine,sub::db)}
{spa::sidecar}"""
    assert combined == expected

    # Test roundtrip parsing
    parsed_clean, parsed_tags, parsed_spaces = split_notes_and_metadata(combined)
    assert parsed_clean == clean
    assert parsed_tags == tags
    assert parsed_spaces == spaces


def test_empty_notes_handling():
    assert split_notes_and_metadata("") == ('', [], {})
    assert split_notes_and_metadata(None) == ('', [], {})
    assert combine_notes_and_metadata("", [], {}) == ""


if __name__ == '__main__':
    test_extract_spaces_standard()
    test_extract_spaces_without_subspaces()
    test_extract_spaces_single_line_multiple()
    test_extract_spaces_whitespace_and_casing()
    test_split_notes_and_metadata()
    test_split_notes_only_spaces()
    test_split_notes_only_tags()
    test_combine_notes_and_metadata_roundtrip()
    test_empty_notes_handling()
    print("All 9 space extractor tests passed successfully!")
