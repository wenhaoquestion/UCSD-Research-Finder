"""Canonical resource URLs; a resource URL is not an entity identifier."""
import html
import re
import urllib.parse


def valid_url(url):
    if not isinstance(url, str) or re.search(r"\s", url):
        return False
    try:
        p = urllib.parse.urlsplit(url)
        return p.scheme in {"http", "https"} and bool(p.hostname) and not p.username and not p.password
    except ValueError:
        return False


def encode_url(url):
    if not isinstance(url, str):
        return url
    try:
        parts = urllib.parse.urlsplit(html.unescape(url.strip()))
        url = urllib.parse.urlunsplit(parts._replace(netloc=parts.netloc.strip()))
    except ValueError:
        return url
    return urllib.parse.quote(url, safe=":/?#[]@!$&'()*+,;=%")


def comparison_key(url):
    """Find possible URI variants for review; never use as ownership proof."""
    url = encode_url(url)
    if not valid_url(url):
        return ""
    p = urllib.parse.urlsplit(html.unescape(url))
    query = urllib.parse.urlencode([(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
                                   if not k.lower().startswith("utm_") and k.lower() not in {"gclid", "fbclid"}])
    path = re.sub(r"/index\.(?:html?|php)$", "", p.path.rstrip("/"))
    return p.netloc.lower().removeprefix("www.") + path + ("?" + query if query else "")


def url_key(url):
    """Identify a transport resource, preserving scheme, host, path and query.

    Empty paths request '/', and fragments are never sent to the server. No
    redirect, hostname alias, default document or tracking behavior is assumed.
    Invalid source strings remain observations, not silently repaired resources.
    """
    if not valid_url(url):
        return ""
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', p.query, ''))
