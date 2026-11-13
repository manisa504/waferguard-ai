# Campaign and portfolio operations

The static project overview and campaign studio are presentation artifacts. Publishing
them does not deploy WaferGuard inference, pass Gate 5, or authorize model promotion.
The current failed qualification remains the source of truth.

## Edit and preview

Edit `DOC/campaign.json` for the daily posts, adaptation outlines, or case-study brief.
Run `python3 scripts/build_campaign.py` to regenerate the portable Markdown handoff.
The page reads the same JSON, so the downloaded brief and visible content stay aligned.

Serve the repository with `python3 -m http.server 8000`, then open
`http://localhost:8000/DOC/` or `http://localhost:8000/DOC/campaign.html`.
Opening the campaign through `file://` cannot reliably fetch its data.

Text uses normal-width system fonts, bounded paragraph lengths, and responsive grids.
No font stretching, text scaling transforms, external font downloads, or generated
dataset imagery are required.

## Video and application link

The original request mentioned a 90-second video and a Vercel app, but neither URL was
supplied. Both `media.videoUrl` and `media.vercelUrl` are null. Do not invent an address.
The campaign page shows explicit pending states, not broken players or disabled links.

When an actual HTTPS video URL is supplied, set `media.videoUrl`. The campaign supports
YouTube watch/short links, numeric Vimeo links, direct MP4/WebM URLs, and a watch link
for other providers. Verify embedding rights, playback, caption availability, and the
actual recording duration. External providers receive requests when their player loads.
Set `media.vercelUrl` only after inspecting the supplied app and checking that campaign
claims match its actual scope. Update the overview's pending section at the same time.

No usable Higgsfield credential was supplied; no Higgsfield generation was attempted.
Keep provider credentials server-side or in ignored local environment configuration.
Never put a provider key in campaign JSON, HTML, Git, or the campaign brief. Generated
decorative media must not be presented as real benchmark examples or model evidence.

## Publication

`.github/workflows/pages.yml` publishes the static site to GitHub Pages on changes to
its inputs on main. It packages only `DOC/` and aggregate `reports/`, plus a root
redirect. It does not upload raw data, models, source runtime, or AWS configuration.
`scripts/build_public_site.py` creates ignored `.public-site/` output.

Hosting follows [GitHub's custom Pages workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
This adds no AWS resources or LinkedIn integration. Existing project CI remains separate.

## Campaign brief

The page copies `CAMPAIGN_BRIEF.md`, including all posts, sources, production notes,
carousels, video script, case study, and approval boundaries. Clipboard access requires
browser permission and a secure context; a Markdown download remains available.

Confirm account, dates, timezone, cadence, and final wording before publication.
The current work does not post or schedule anything on LinkedIn. Do not imply that an
unavailable Clarity skill was applied: it was searched for but not installed. The copy
instead follows the requested business-first sequence and plain-language requirements.
