"""Build the one-page reconnaissance note as PDF and a matching PNG preview."""

from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "reconnaissance" / "reconnaissance_note.pdf"
PREVIEW_PATH = ROOT / "tmp" / "pdfs" / "reconnaissance_note_preview.png"

NAVY = "#17324D"
BLUE = "#2F6690"
PALE_BLUE = "#EAF2F8"
GOLD = "#E8A317"
DARK = "#202A33"
MUTED = "#5D6973"


def wrapped(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def add_section(
    fig,
    x,
    y,
    width,
    title,
    paragraphs,
    wrap_width=48,
    font_size=8.05,
    line_step=0.0166,
    paragraph_gap=0.009,
    title_gap=0.025,
):
    fig.text(x, y, title.upper(), color=BLUE, fontsize=9.1, fontweight="bold", va="top")
    fig.add_artist(Rectangle((x, y - 0.008), width, 0.002, transform=fig.transFigure,
                             color=GOLD, linewidth=0))
    cursor = y - title_gap
    for paragraph in paragraphs:
        text = wrapped(paragraph, wrap_width)
        line_count = text.count("\n") + 1
        fig.text(x, cursor, text, color=DARK, fontsize=font_size, va="top", linespacing=1.22)
        cursor -= line_count * line_step + paragraph_gap
    return cursor


def build() -> None:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(8.27, 11.69), facecolor="white")
    canvas = fig.add_axes([0, 0, 1, 1])
    canvas.axis("off")

    canvas.add_patch(Rectangle((0, 0.875), 1, 0.125, color=NAVY, linewidth=0))
    fig.text(0.065, 0.952, "JUMIA NIGERIA RECONNAISSANCE", color="white",
             fontsize=19, fontweight="bold", va="top")
    fig.text(0.065, 0.916,
             "UCU Data Mining and Wrangling | Group 2 | Verified 13 October 2026",
             color="#DDEAF3", fontsize=9.3, va="top")
    fig.text(0.065, 0.892,
             "Purpose: confirm access rules, page structure and a responsible collection plan before scraping.",
             color="white", fontsize=8.4, va="top")

    canvas.add_patch(Rectangle((0.055, 0.787), 0.89, 0.068, color=PALE_BLUE, linewidth=0))
    fig.text(0.07, 0.839, "VERIFIED CATEGORY PAGES", color=BLUE, fontsize=8.8,
             fontweight="bold", va="top")
    fig.text(0.07, 0.818,
             "Phones & Tablets  https://www.jumia.com.ng/phones-tablets/",
             color=DARK, fontsize=8.0, va="top")
    fig.text(0.52, 0.818, "Computing  https://www.jumia.com.ng/computing/",
             color=DARK, fontsize=8.0, va="top")
    fig.text(0.07, 0.797, "Electronics  https://www.jumia.com.ng/electronics/",
             color=DARK, fontsize=8.0, va="top")

    left_x, right_x, column_width = 0.065, 0.525, 0.41

    left_y = 0.758
    left_y = add_section(fig, left_x, left_y, column_width, "Robots.txt and ethics", [
        "robots.txt returned HTTP 200. Its public-site guidance permits clearly identified bots with an owner/contact when they stay below 200 requests per minute.",
        "The User-Agent identifies DSC2107-UCU-Group-2 and states that contact is supplied at runtime; this document does not print the email address.",
        "Private/customer/cart paths, site search, tracking parameters, filters and crawl traps remain disallowed. Standard category pages and ?page=N pagination were checked as allowed.",
    ])
    left_y = add_section(fig, left_x, left_y - 0.006, column_width, "Technical approach", [
        "Product data is server-rendered HTML. Each successful category page exposed 40 main catalogue cards, so Requests plus BeautifulSoup is sufficient. Playwright and private/mobile endpoints are unnecessary.",
        "Main card: article.prd._fb.col.c-prd. Stable ID and brand: a.core[data-gtm-id] and data-gtm-brand. Name, prices, discount, rating and reviews use h3.name, div.prc, div.old, div.bdg._dsct, div.stars and div.rev.",
    ])
    add_section(fig, left_x, left_y - 0.006, column_width, "Pagination and timestamps", [
        "Next-page links use ?page=2#catalog-listing; the HTTP request needs only ?page=2 and then increasing page numbers.",
        "Every observation receives a genuine timezone-aware Africa/Nairobi timestamp and collection date. Missing values remain missing rather than becoming zero.",
    ])

    right_y = 0.758
    compact = {
        "wrap_width": 52,
        "font_size": 7.55,
        "line_step": 0.0138,
        "paragraph_gap": 0.0045,
        "title_gap": 0.021,
    }
    right_y = add_section(fig, right_x, right_y, column_width, "Required observations", [
        "Stable product ID, product name, brand, raw current and old prices, displayed discount, rating, review count, assigned category, canonical URL, NGN currency, source site, scraped_at and scrape_date.",
        "Cross-category repeats are deduplicated by stable ID while category membership is preserved.",
    ], **compact)
    right_y = add_section(fig, right_x, right_y - 0.004, column_width, "Rate and request estimate", [
        "Requests are sequential with a fixed three-second delay - about 20 requests per minute, well below the published 200-per-minute ceiling. The run also keeps a request counter and a 1,000-request safety limit.",
        "Sample estimate: robots.txt plus one page from each category = about 4 requests and about 120 cards. Daily estimate: robots.txt plus about five pages per category = about 16 requests for roughly 600 cards, with limited retries if needed.",
    ], **compact)
    right_y = add_section(fig, right_x, right_y - 0.004, column_width, "Known challenges", [
        "Old price, discount, rating and review count can be genuinely absent. Products can overlap categories, promotions can change HTML, and temporary network failures can occur.",
        "A Computing request returned a preserved HTTP 503 maintenance page; a later polite request returned HTTP 200. Production logic therefore uses bounded retries and controlled back-off, but stops on CAPTCHA, HTTP 403, HTTP 429 or explicit denial.",
    ], **compact)
    add_section(fig, right_x, right_y - 0.004, column_width, "Evidence and decision", [
        "Evidence is stored under reconnaissance/evidence/: robots.txt, HTTP metadata, timestamps, response sizes and SHA-256 hashes. Large HTML captures remain local and outside Git.",
        "Decision: use a polite, sequential Requests/BeautifulSoup scraper and validate a 100-product sample before any full daily run.",
    ], **compact)

    canvas.add_patch(Rectangle((0.055, 0.035), 0.89, 0.036, color=NAVY, linewidth=0))
    fig.text(0.07, 0.053,
             "Responsible collection only | No login | No CAPTCHA bypass | No personal information",
             color="white", fontsize=8.0, va="center")
    fig.text(0.93, 0.053, "1", color="white", fontsize=8.0, ha="right", va="center")

    fig.savefig(PDF_PATH, format="pdf", dpi=300, bbox_inches=None, metadata={
        "Title": "Jumia Nigeria Reconnaissance Note",
        "Author": "UCU Data Mining and Wrangling - Group 2",
        "Subject": "Responsible web-scraping reconnaissance",
    })
    fig.savefig(PREVIEW_PATH, format="png", dpi=170, bbox_inches=None)
    plt.close(fig)

    print(PDF_PATH)
    print(PREVIEW_PATH)


if __name__ == "__main__":
    build()
