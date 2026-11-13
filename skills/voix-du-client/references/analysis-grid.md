# Analysis grid

## 1. Starting taxonomy (e-commerce / retail)

Use it as a starting point, then merge, split or rename themes so they fit the data.
Prefer the customer's words for theme names ("Colis arrivé abîmé" rather than "Logistics issue").

| Family | Typical themes |
|---|---|
| Product | quality, conformity to description, efficacy, texture/smell (cosmetics), size/fit, durability, ingredients/composition |
| Price & value | price level, promotions, perceived value, shipping fees, hidden costs |
| Ordering | website/app usability, payment, stock availability, account, promo codes |
| Delivery | delay, tracking, damaged parcel, lost parcel, carrier behaviour, pick-up points |
| Returns & refunds | return process, refund delay, exchange, return fees |
| Customer service | reachability (wait time, channel), competence, empathy, follow-up, resolution at first contact |
| Communication | e-mails/SMS frequency, clarity of information, unsubscribe |
| Brand & values | packaging/eco-design, ethics, origin, trust |

For call transcripts, add: reason for call, first-contact resolution, repeated contacts,
agent behaviour (empathy, ownership), procedural friction (identity checks, transfers).

## 2. Coding rules

- Unit of count = one verbatim. A verbatim can carry 1-3 themes.
- A theme needs at least 2 verbatims; otherwise keep it as "other" or as a weak signal.
- Keep a running list `theme -> [ids]` while reading, it gives you counts and quotes.
- Separate **what happened** (fact: "parcel arrived 10 days late") from **how it felt**
  (emotion: "furious, it was a gift").
- Mixed reviews ("great cream, but delivery was a nightmare") feed one delight theme and
  one pain-point theme.

## 3. Sentiment

| Label | Rule of thumb |
|---|---|
| positive | satisfaction without reservation |
| mixed | clear positive and negative elements |
| neutral | factual, no evaluation |
| negative | dissatisfaction dominates (including sarcasm: "Bravo, 3 weeks for a parcel") |

Ratings and text can disagree (5 stars + complaint): trust the text and report the gap.

## 4. Emotions

Use a short, business-friendly list: **frustration, anger, disappointment, worry/anxiety,
confusion, resignation, relief, satisfaction, delight, trust**. One dominant emotion per
verbatim. Resignation ("I won't bother complaining anymore") is a strong churn predictor:
always highlight it.

## 5. Intensity scale (pain points)

| Level | Meaning | Clues |
|---|---|---|
| 1 | Mild annoyance | "a bit", "shame that", no consequence |
| 2 | Noticeable irritation | repeated, but customer still satisfied overall |
| 3 | Clear dissatisfaction | rating <= 3, explicit criticism, extra effort for the customer |
| 4 | Strong dissatisfaction | anger, several contacts, refund demand, "never again" |
| 5 | Rupture / risk | churn stated, public escalation threat, legal words, health or safety issue |

The intensity of a theme is the **typical** (median) intensity of its verbatims, not the maximum.
Mention the extreme cases separately if they matter.

## 6. Choosing quotes

- 2-3 per theme, 1-3 sentences each, verbatim (spelling kept), already pseudonymised.
- Representative of the theme, varied (channel, rating, period).
- Prefer quotes that show the consequence for the customer ("I had to call 4 times").
