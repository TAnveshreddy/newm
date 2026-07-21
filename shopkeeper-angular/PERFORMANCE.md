# Performance testing — shopkeeper-angular

Measured on the **production build** (`ng build --configuration=production`),
served with gzip, in headless Chromium (Playwright), median of 5 cold runs.

## Bundle budget (production)

| Group | Raw | Gzip (transfer) |
|---|---|---|
| **Initial total** | 802.9 kB | **215 kB** |
| ↳ Firebase (auth + firestore) chunk | 571 kB | 151 kB |
| ↳ Angular runtime chunk | 104 kB | 26 kB |
| ↳ app `main` | 71.6 kB | 19 kB |
| ↳ polyfills (zone.js) | 34.5 kB | 11 kB |
| ↳ global styles | 12.5 kB | 2.9 kB |
| Largest lazy route (dashboard) | 13.5 kB | 4.5 kB |
| Smallest lazy route (reports) | 3.3 kB | 1.4 kB |

Every feature is code-split into its own lazy chunk (dashboard, inventory,
billing, transactions, parties, admin, settings, reports, login), fetched only
on first navigation.

## Load metrics

### Localhost, uncompressed (upper bound of the app itself)
| FCP | LCP | DCL | Load | TBT | Heap | Requests |
|---|---|---|---|---|---|---|
| 188 ms | 188 ms | 108 ms | 109 ms | **0 ms** | 9.2 MB | 13 |

### Realistic: gzip, ~12 Mbps / 40 ms RTT, 4× CPU slowdown (mid-tier laptop)
| FCP | LCP | DCL | Load | TBT | Transfer | Requests |
|---|---|---|---|---|---|---|
| 864 ms | 864 ms | 518 ms | 523 ms | 202 ms | 250 kB | 13 |

**Interpretation** (Core Web Vitals thresholds):
- **LCP 0.86 s** — well within "Good" (< 2.5 s).
- **TBT ~200 ms** — at the "Good / Needs-improvement" boundary; caused by
  parsing/evaluating the eager Firebase chunk during startup.
- **Transfer 250 kB / 13 requests** — lean; no render-blocking third parties.
- Maps to an estimated Lighthouse Performance score in the **low-to-mid 90s**.

## What's already optimal
- Production build: AOT, minification, tree-shaking, `outputHashing` for
  long-term caching.
- **Route-level code-splitting + lazy loading** — initial JS carries no feature
  code.
- **OnPush** change detection on components + **signals** — minimal re-render
  work (TBT 0 ms on an unthrottled CPU).
- `provideHttpClient(withFetch())`; Firestore **offline persistent cache**
  (repeat loads read from disk, not the network).

## Applied optimization
- **`preconnect`/`dns-prefetch`** to the Firebase auth & Firestore hosts in
  `index.html`, so DNS+TCP+TLS to those endpoints complete during first paint
  and the first post-login API round-trips are faster.

## Recommended next optimizations (by impact)
1. **Defer Firestore** — the ~150 kB (gz) Firebase chunk loads eagerly at
   bootstrap, but Firestore isn't needed until *after* login. Moving the
   Firestore provider (and the data services that depend on it) behind the
   authenticated shell route would cut the initial bundle roughly in half and
   drop TBT below 150 ms. (Auth must stay eager for the route guard.)
2. **Zoneless change detection** (`provideExperimentalZonelessChangeDetection`)
   — the app is already signals-first; removing `zone.js` saves ~11 kB (gz)
   and reduces scheduling overhead. Verify OTP/async flows first.
3. **Route-level preloading** — add `withPreloading(PreloadAllModules)` (or a
   network-aware strategy) so idle bandwidth warms feature chunks after the
   shell paints, making in-app navigation instant.
4. **Self-host the font stack** (already system-ui — no web-font cost) and keep
   images as inline SVG (already done) to avoid extra requests.

## How to reproduce
```bash
npm run build
# serve dist/shopkeeper-angular/browser with any gzip-enabled static server,
# then run Lighthouse or a Playwright navigation-timing script against it.
```
