# Data dictionary

| Column | Cleaned type | Source | Meaning |
|---|---:|---|---|
| `source_product_id` | text | `a.core[data-gtm-id]` | Stable Jumia catalogue identifier. |
| `product_name` | text | `h3.name` | Product title displayed in the listing. |
| `brand` | text/nullable | `a.core[data-gtm-brand]` | Jumia's displayed/encoded brand. |
| `current_price` | decimal/nullable | cleaned `div.prc` | Current selling price in NGN. |
| `old_price` | decimal/nullable | cleaned `div.old` | Previous price when Jumia displays one. |
| `displayed_discount_percentage` | decimal/nullable | cleaned discount badge | Discount percentage shown by Jumia. |
| `calculated_discount_percentage` | decimal/nullable | derived | `(old_price-current_price)/old_price*100`. |
| `rating` | decimal/nullable | `div.stars` | Rating on a 0–5 scale when displayed. |
| `review_count` | integer/nullable | `div.rev` | Number of displayed reviews. |
| `category` | text | collection configuration | One or more assigned categories separated by ` | `. |
| `product_url` | text | `a.core[href]` | Canonical public Jumia product URL. |
| `currency` | text | project configuration | `NGN`. |
| `source_site` | text | project configuration | `Jumia Nigeria`. |
| `scraped_at` | timezone-aware text | collection clock | Genuine observation time in ISO 8601 format. |
| `scrape_date` | date text | collection clock | Africa/Nairobi calendar date. |
| `discount_difference_flag` | text | derived validation | Marks a displayed/calculated difference over 2 percentage points. |
| `validation_flags` | text | derived validation | Records impossible values without replacing them with zero. |

The raw CSV uses `_raw` price, discount, rating and review fields so the exact
displayed text remains available. Cleaning writes a separate file and never
edits the raw input.

