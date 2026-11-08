"""Validate metadata, local navigation, publishing files, disclosures and the legal notice."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids=set(); self.links=[]; self.meta={}; self.canonical=[]; self.title=False
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get("id"): self.ids.add(a["id"])
        if tag=="title": self.title=True
        if tag=="meta": self.meta[a.get("name",a.get("property",""))]=a.get("content","")
        if tag=="link" and a.get("rel")=="canonical": self.canonical.append(a.get("href"))
        for key in ("href","src"):
            if a.get(key): self.links.append(a[key])

paths=["index.html"]
texts={p:(ROOT/p).read_text() for p in paths}
pages={p:Page(t) for p,t in texts.items()}
for path, page in pages.items():
    expected="https://kayakcartel.com/"
    assert page.title and page.meta.get("description"), path+": missing metadata"
    assert page.canonical==[expected], path+": incorrect canonical"
    assert page.meta.get("og:url")==expected and page.meta.get("og:title") and page.meta.get("twitter:card"), path+": missing share metadata"
    for link in page.links:
        u=urlsplit(link)
        if u.scheme or u.netloc: continue
        target=(ROOT/unquote(u.path.lstrip("/")) if u.path.startswith("/") else (ROOT/path).parent/unquote(u.path)) if u.path else ROOT/path
        target=target.resolve()
        assert target.is_relative_to(ROOT.resolve()), link
        if target.is_dir(): target=target/"index.html"
        assert target.is_file(), path+": missing "+link
        if u.fragment and target.suffix==".html":
            other=pages.get(str(target.relative_to(ROOT))) or Page(target.read_text())
            assert unquote(u.fragment) in other.ids, path+": broken fragment "+link
assert (ROOT/"CNAME").read_text().strip()=="kayakcartel.com"
assert "Sitemap: https://kayakcartel.com/sitemap.xml" in (ROOT/"robots.txt").read_text()
urls={n.text for n in ET.parse(ROOT/"sitemap.xml").findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")}
assert urls=={"https://kayakcartel.com/"}
assert 'Booking preview' in texts["index.html"] and 'This search is a preview' in texts["index.html"], "Keep booking preview disclosure"
assert 'Nothing is sent until you send that email' in texts["index.html"], "Keep email submission disclosure"
assert "not a registered corporation" in texts["index.html"] and "belong to Andrew Jourdan" in texts["index.html"], "Keep the on-page legal notice (unregistered business, domain ownership)"
assert "Nothing on this site is an offer to sell a franchise" in texts["index.html"], "Keep the franchise no-offer disclaimer"
print("PASS: page, local links, metadata, publishing files, preview disclosures and legal notice")
