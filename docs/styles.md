# Slide styles

`cgimg` expands your prompt with your ChatGPT account's text model before drawing
(when `enhance=True`, the default). The `style` argument picks the design treatment.
Implemented in `src/cgimg/engine/enhance.py`.

## The three styles

| Style | Look | When to use |
|-------|------|-------------|
| `auto` | General. A dense professional **infographic** for a concept/topic, or a vivid **photographic** prompt if the request names a real scene. | One-off images, photos, or generic infographics. The default for `generate_image`. |
| `slide` | Clean **editorial** presentation slide: white/cream background with a subtle accent wash, dark navy text, ONE warm accent color, soft rounded cards with line icons, one glossy 3D hero illustration, a small "Slide" pill, and a slim bottom takeaway banner. | Polished decks with a calm, light, premium feel. The default for `generate_slide_deck`. |
| `fintech` | Premium **light-blue dashboard**: blue-to-white gradient background, glassmorphism cards, circular blue-gradient icon badges, navy headings with a blue accent, optional friendly 3D robot mascot and a glass dashboard with donut/line charts, and a blue bottom banner with a shield icon. | AI / finance / product-keynote decks that want a modern tech look. |

## Content richness (`slide` and `fintech`)

For `slide` and `fintech`, enhancement **always runs** (the ≥280-char skip used by
`auto` is bypassed) and the content is completed into a **full, information-rich slide**:

- **Every main point gets a bold label plus a 2-line supporting description** (~12–22
  words) — never a bare list of labels.
- **Sparse input is intelligently completed** into a sensible, full slide on the topic.
- Supporting elements are added to fill the slide: a row of 4–6 application/benefit chips,
  a small stat/dashboard card or chart, and a one-line takeaway banner.
- The image prompt **explicitly demands all text be rendered in full** (not dropped or
  abbreviated), while staying clearly legible — not a wall of tiny text, not nearly empty.
- **No fabricated statistics** — any added numbers/charts are clearly illustrative.

`auto` does not force this content completion: it produces a general infographic or photo,
and skips enhancement entirely when the prompt is already long (≥280 chars).

## CLI examples

```bash
# clean editorial slide
uv run cgimg gen "AI agents for customer support" --style slide

# light-blue fintech dashboard slide
uv run cgimg gen "real-time fraud detection pipeline" --style fintech

# a whole deck (one slide per prompt) — generate_slide_deck defaults to slide style
uv run cgimg gen "What is RAG?" --style slide --out out
```

## Notes

- If the text round-trip fails for any reason, `enhance_prompt` never raises — it falls
  back to a deterministic per-style template wrapper that still encodes the look and the
  content-richness rules.
- Brand context (used by `branded_deck` / `styled_deck`) forces enhancement to run as well
  and appends instructions to use exact brand colors and/or to keep a logo corner clear.
