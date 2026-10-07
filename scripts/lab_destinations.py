"""Shared, conservative exclusions for URLs that cannot identify a lab site.

These checks reject destinations, not statements about whether a lab exists.
A news article may be useful discovery evidence, but it is not a lab homepage.
"""
import re
import urllib.parse


NEWS_HOSTS = {"ucsdnews.ucsd.edu", "washingtonpost.com", "kusi.com"}
NEWS_PATH = re.compile(r"/(?:news|newsroom|news-releases?|press-releases?)(?:/|$|\.(?:html?|aspx)$)", re.I)


def nonlab_destination_reason(url):
    """Return a rejection reason, or an empty string if not ruled out here."""
    if not isinstance(url, str) or not url or re.search(r"[\s\x00-\x1f\x7f]", url):
        return "Malformed or non-HTTP lab destination URL."
    try:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return "Malformed or non-HTTP lab destination URL."
        parsed.port  # Validate malformed port values as well.
    except ValueError:
        return "Malformed or non-HTTP lab destination URL."
    path = urllib.parse.unquote(parsed.path).lower()
    if "://" in path:
        return "Malformed lab destination URL contains an embedded URL scheme in its path."
    host = parsed.hostname.lower().rstrip(".")
    if any(host == domain or host.endswith("." + domain) for domain in NEWS_HOSTS) or NEWS_PATH.search(path):
        return "News or press-release destination is not a laboratory website."
    return ""
