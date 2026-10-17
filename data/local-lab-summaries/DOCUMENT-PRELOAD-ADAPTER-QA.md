# Document-preload adapter QA

**PASS**, reviewed 2026-10-16T05:28:56+00:00. No actionable issue. Exact supplied adapter pin `f8d71d075a96ccf22f25a8cf4d5ca24e7a65250c3805c726b8a86237cf0a79ae` and new test pin `9dbcb51c64d594bd02797128d8f5154f1de7910a5281d68856a1971231753280` match actual files.

Relative to `641fd9abbcdc2cc3382847acb241695384a0faec` (adapter `2e691409…`), only `plan()` changes. Removing that definition leaves the entire module AST identical. The loader/public-origin adapter, TLS and transport, shared gate, robots, retries/deadlines, one-shot state, 2M/8M limits and execution authorization are unchanged.

The new branch requires an explicit reviewed entry bound to an existing sourceId, actual zoned source observation/review dates, matching packet/review SHA and actual cached bytes, and an ok root with no explicit access boundary. It admits only an actual parsed `link` with a `preload` rel token, `as=document`, and exact nonempty literal href. Resolution against the source URL must equal the target’s strict request key, retaining scheme, www, port, path and query, and the host must match the source host. Existing public-origin and transport checks still apply. This is discovery only; no JavaScript evaluation, lab acceptance, science, redirect or canonical migration is introduced.

Independent offline suites passed **64/64**: document preload **10**, frame discovery **13**, shared adapter **11**, original URI scope **30**. Cases reject scripts, script strings, comments, CSS pseudo-tags, anchors/images, non-document preloads, missing/altered literal href, source/date/hash drift, changed bytes, host/credential/scheme/port/path/query spoofing and robots/auth/challenge/prior boundaries. The mutation test leaves raw/packet science and original root observations unchanged. I did not rerun the full 209/331 suite; those broader totals are not claimed as my results.

The actual Romero binding passes every guard. Source `src-04a051aebaebcc7c` was requested/final at [the actual root](http://r2g.ucsd.edu/), observed **2026-10-16T04:57:07+00:00**, body SHA `25c774bbc43f61f0d282c3cd44b9a1f796bf24ba6e44c3a00b0aed43d355b707`. The actual cached HTML contains:

```html
<link rel="preload" href="home.html" as="document">
```

It resolves exactly to [the curated target](http://r2g.ucsd.edu/home.html). The entry’s review time is **2026-10-16T05:25:54+00:00** and its source ID/time/hash match both packet and bytes; `source_matches_fetch` also passes. The root’s image/style preloads, stray anchor-looking CSS and `window.location.href` code are not admission evidence. No target body was fetched or accepted by this review.

At receipt inspection, the existing verification (checked 05:21:06) still pinned the prior `2e691409…` adapter. This is the expected fail-closed state while the parent prepares fresh process/dependency pins, tests and receipt for `f8d71d07…`. I did not refresh or enable execution.

0 network requests; 0 production plan calls. Only this Markdown and its JSON companion were written. No production code, source, packet, raw record, collector, plan or network receipt was changed.

