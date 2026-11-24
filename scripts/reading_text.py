"""Visible summary text shared by reading estimates and section search."""
import math
import re


def paragraph_text(item):
    if isinstance(item, str):
        return item
    if 'list' in item:
        return ' '.join(part['l'] + ' ' + part['t'] for part in item['list'])
    return item.get('image', {}).get('caption', '')


def section_text(section):
    return ' '.join([section['h']] + [paragraph_text(p) for p in section['p']])


def reading_minutes(record):
    # Approximation: 500 non-whitespace characters/minute. Excludes source video,
    # timestamps, editorial notes and practice blocks not rendered on the page.
    parts = []
    for block in record.get('intro', []):
        if block['kind'] == 'points':
            parts.append(block['h'])
            parts.extend(p if isinstance(p, str) else p['l'] + ' ' + p['t'] for p in block['items'])
    parts.extend(section_text(section) for section in record.get('detail', []))
    length = len(re.sub(r'\s+', '', ' '.join(parts)))
    return max(1, math.ceil(length / 500)) if length else None
