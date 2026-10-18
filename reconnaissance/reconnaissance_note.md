# Jumia Nigeria reconnaissance note

**Project:** Uganda Christian University, Data Mining and Wrangling, Group 2

**Reconnaissance time:** 13 October 2026, 18:30–18:42 Africa/Nairobi

**Website:** https://www.jumia.com.ng/

## Starting pages and access rules

The verified category pages are:

- Phones & Tablets: `https://www.jumia.com.ng/phones-tablets/`
- Computing: `https://www.jumia.com.ng/computing/`
- Electronics: `https://www.jumia.com.ng/electronics/`

`https://www.jumia.com.ng/robots.txt` returned HTTP 200 at
`2026-10-13T18:30:12+03:00`. Its public-site comments permit scraping when the
bot clearly identifies itself and its owner/contact and stays below 200
requests per minute. The `User-agent: *` rules disallow private/customer/cart
paths, `/mobapi/`, site search, many filter parameters, tracking parameters,
and crawl traps. The three plain category URLs and their `?page=2` URLs were
checked as allowed. This project uses about 20 requests per minute: one
sequential request every three seconds.

## Technical findings

Product data is present in server-rendered HTML, so `requests` and
BeautifulSoup are the simplest reliable tools. Playwright and private/mobile
endpoints are unnecessary. Each successful first category page contained 40
main catalogue cards selected by `article.prd._fb.col.c-prd`. The next-page
links use `?page=2#catalog-listing`; requests only need `?page=2`.

Reliable fields are:

- stable product ID: `a.core[data-gtm-id]`
- name: `h3.name`
- brand: `a.core[data-gtm-brand]`
- URL: `a.core[href]`
- current price: `div.prc`
- old price: `div.old` when displayed
- discount: `div.bdg._dsct` when displayed
- rating: `div.stars` when displayed
- review count: trailing parenthesised text inside `div.rev`

The scraper adds the assigned category, `NGN`, source name, genuine
timezone-aware timestamp, and Africa/Nairobi collection date. Missing old
prices, discounts, ratings, or review counts remain missing rather than zero.

## Request estimate and challenges

The 100-product sample needs one listing page from each category plus one
robots request: normally four requests. About five pages per category provide
roughly 600 cards, so a normal Daily Run needs about 16 requests including
robots.txt. An extra balanced page round may be used if cross-category overlap
keeps the unique total below 600. This is far below the 1,000-request project
limit.

Possible challenges are missing optional fields, products appearing in more
than one category, changing promotional HTML, and temporary server errors. A
Computing request at `2026-10-13T18:30:26+03:00` returned a genuine HTTP 503
maintenance page. It was preserved and no bypass was attempted; a later polite
request returned HTTP 200. The production client therefore uses bounded 5xx
retries and controlled back-off. It stops on CAPTCHA, HTTP 403, HTTP 429, or
explicit access-denial text.

## Required fields and evidence

The raw collection keeps all 14 requested fields: product ID, name, brand,
four raw price/discount fields, raw rating and review count, category, product
URL, currency, source site, timestamp, and date.

Evidence is stored in `reconnaissance/evidence/`:

- exact `robots_20261013T183012+0300.txt`
- exact first-page HTML captures for all three categories
- `reconnaissance_http_20261013T183147+0300.json`, including the 503
- `reconnaissance_http_20261013T184214+0300.json`, including successful
  Computing and Electronics responses, timestamps, sizes, and SHA-256 hashes

Full HTML captures are retained as working evidence because they preserve the
page structure used by the parser. They should be excluded from the lean final
submission because they are large, change frequently, and are not source code.

## Day 6 live-policy recheck

The access and selector checks were repeated before Daily Run 6 on 18 October
2026. `robots.txt` returned HTTP 200 at `21:36:49+03:00` with SHA-256
`375a7c8fa4ea1d2c343ea66b16672bb37b8935b42ff82e20a7d612588d77469e`.
The first Phones & Tablets, Computing and Electronics pages also returned HTTP
200 and each contained 40 main catalogue cards, a next-page link and no CAPTCHA
or access-denial signal. The exact recheck is recorded in
`reconnaissance_http_20261018T213742+0300.json` and its accompanying robots and
HTML captures. The subsequent live test and sample therefore continued with
the approved sequential three-second delay.

