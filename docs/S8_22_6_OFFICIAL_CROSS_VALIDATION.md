# S8.22.6 — NBA official opening-night schedule cross-validation

Official NBA 2023-24 schedule announcement published August 2023 lists two opening-night games on 2023-10-24: Lakers at Nuggets 7:30pm ET, Suns at Warriors 10:00pm ET. NBA game pages identify 0022300061 and 0022300062 respectively. The reference is curated and must not be misrepresented as raw captured official schedule bytes.

NBA sources:
- https://www.nba.com/news/2023-24-nba-regular-season-schedule
- https://www.nba.com/game/lal-vs-den-0022300061
- https://www.nba.com/game/phx-vs-gsw-0022300062

S8.22.6 provides date-scoped offline comparison of user-supplied provider rows with this curated official reference, preserving source CSV SHA256, and refusing automatic crosswalk promotion. Unknown/missing mappings, duplicates, other-date contamination and tipoff mismatch are surfaced or fail closed. It does not certify historical as-of data, player eligibility, source entitlement, or multi-date coverage. RESEARCH_ONLY / BLOCK_TRAINING.
