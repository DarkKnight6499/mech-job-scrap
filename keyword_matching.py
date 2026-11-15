"""Word-boundary matching with engineering phrase and acronym aliases."""
import functools
import re

# Config
ALIASES = {
    "computer aided design": "cad",
    "computer-aided design": "cad",
    "research and development": "r&d",
    "research & development": "r&d",
    "unmanned aerial vehicle": "uav",
    "printed circuit board": "pcb",
    "human machine interface": "hmi",
    "human-machine interface": "hmi",
    "supervisory control and data acquisition": "scada",
    "cooperative education": "co-op",
}


def _term_variants(term):
    key = term.lower()
    variants = {term}
    if key in ALIASES:
        variants.add(ALIASES[key])
    else:
        for full, short in ALIASES.items():
            if key == short:
                variants.add(full)
    return variants


@functools.lru_cache(maxsize=None)  # re's own cache holds 512; the exclude lists now exceed that and thrash
def _pattern(term):
    escaped = re.escape(term)
    return re.compile(r"(?<![A-Za-z0-9])" + escaped + r"(?![A-Za-z0-9])", re.IGNORECASE)


def contains_term(text, term):
    return any(_pattern(v).search(text) for v in _term_variants(term))


@functools.lru_cache(maxsize=64)
def _combined(terms):
    variants = set()
    for term in terms:
        variants |= _term_variants(term)
    alt = "|".join(re.escape(v) for v in sorted(variants, key=len, reverse=True))
    return re.compile(r"(?<![A-Za-z0-9])(?:" + alt + r")(?![A-Za-z0-9])", re.IGNORECASE) if alt else None


def contains_any(text, terms):
    """Same result as any(contains_term(text, t) for t in terms), in one regex pass (lists hold 600+ terms)."""
    rx = _combined(tuple(terms))
    return bool(rx and rx.search(text))


def first_match(text, terms):
    """The text that made contains_any() true (an alias variant of the term can match), or None; names the rule that hid a role."""
    rx = _combined(tuple(terms))
    m = rx.search(text) if rx else None
    return m.group(0) if m else None
