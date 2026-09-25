# CHANDRABHAR-2 — Color Palette

Values below were sampled directly from `logo.png` (the supplied official mark) and rounded to
usable UI tokens. They are used consistently across the dashboard, documentation, and
presentation assets.

| Token | Hex | Sampled from | Usage |
|---|---|---|---|
| Mission Black | `#05070A` | Logo background | App background, primary dark surface |
| Panel Black | `#0B0F16` | Derived (lighter black) | Card / panel surfaces |
| Chandrabhar Orange | `#F97316` | Rocket flame / wordmark accent (~`#FC7A0C`) | Primary accent, CTAs, active states |
| Orbit Blue | `#1B6FD6` | Satellite solar panels (~`#125AAE`) | Secondary accent, links, info states |
| India Green | `#138808` | Tricolour swoosh (~`#008C41`, adjusted to the standard Ashoka Chakra flag green) | Success / VALIDATED status |
| Lunar White | `#F5F7FA` | Wordmark, stars (~`#FAF9F9`) | Primary text on dark surfaces |
| Neutral Grey | `#8A94A6` | Derived | Secondary/muted text, borders |
| Warning Amber | `#FFC24B` | Derived (between orange and gold) | INSUFFICIENT_EVIDENCE / caution states |
| Alert Red | `#FF6B6B` | Derived | FAILED states, errors |

## Usage rules

- **Colour is used sparingly.** The interface is dark, technical, and text-first; orange and blue
  are reserved for emphasis (active tab, primary button, status badges), not decoration.
- **Never colour-only.** Every status (VALIDATED / INSUFFICIENT_EVIDENCE / FAILED / RUNNING /
  WAITING) is paired with a text label and/or icon, not colour alone, for accessibility.
- Saffron/white/green are used together only in the tricolour accent rule under the wordmark —
  they are not used as general-purpose UI colours, to avoid trivializing the national flag
  association.
- Backgrounds stay near-black (`Mission Black` / `Panel Black`); pure white backgrounds are not
  used anywhere in the product.
