# S8.22.7.7 — Official date-level NBA games extraction

The user archived `https://www.nba.com/games?date=2023-11-15` with S8.22.7.2. Receipt SHA-256 `85ea943f3b9cba374728ba6c37f05848bbbe2b34bbd4956ceda367d0c66ae0f4`, 506293 bytes, retrieval `2026-10-10T01:11:42.998766+00:00`. Verified byte-for-byte against the uploaded source.

The HTML `__NEXT_DATA__` payload contains eight `gameCardFeed.modules[0].cards[].cardData` records, official IDs `0022300192` through `0022300199`. The runner validates the archived bytes, extracts official ID, home/away tricodes, and UTC tipoff. The date listing's eight records agree in **count** with the eight provider rows previously reported. **Provider matchup and tipoff agreement is not yet established** without the original provider snapshot and field schema. Even after matchup agreement, date completeness and historical as-of remain uncertified.

No routine collection, no model training, no historical availability certification.
