# S8.22.7.12 — independent slate evidence acquisition

One **manual** unauthenticated retrieval of a dated third-party TV listing, followed by offline original-byte archive and matchup comparison. No automatic network calls or retries in the validator. Only retrieve if permitted by site terms; if blocked, stop and use browser Save Page As (HTML) if permitted. Do not bypass access controls.

Source: https://sportsgamestoday.com/2023-11-15-wednesday-sports.php

Use the PowerShell commands provided with this patch. Input is raw HTML bytes, not copied text. Parser expects a table section headed `NBA REGULAR SEASON` with `Away at Home` rows. Site markup changes must be reviewed rather than silently fixed. Never certify completeness/as-of or enable training based on this source alone.
