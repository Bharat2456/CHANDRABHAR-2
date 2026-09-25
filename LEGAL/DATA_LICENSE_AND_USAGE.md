# Data License and Usage

## Scope

This document covers **Chandrayaan-2 mission data**, which is entirely separate from
CHANDRABHAR-2's own software license status (see [`LICENSE.md`](LICENSE.md)) and from
third-party software licenses (see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)).

## No data is included

This repository does not include, bundle, or redistribute any Chandrayaan-2 mission data. The
dashboard and CLI operate only on data the user has separately obtained and stored locally.

## Source and terms

Chandrayaan-2 data (OHRC, TMC-2, IIRS products) is distributed by ISRO through the PRADAN portal
operated by ISSDC: **https://pradan.issdc.gov.in/ch2/**. This is an external reference — the
authoritative, current terms live there, not in this document, and **must be verified there**
before any use beyond personal experimentation, and certainly before any commercial or
redistribution use.

Based on the PRADAN portal's own stated disclaimer (verify current wording at the source before
relying on this summary): Chandrayaan-2 data is supplied for non-commercial scientific use, and
is not licensed for commercial use, by ISRO/PRADAN. This project does not grant, alter, or waive
any of those terms.

## What CHANDRABHAR-2's software license does not do

Whatever software license is eventually confirmed for the CHANDRABHAR-2 codebase (see
[`LICENSE.md`](LICENSE.md)) governs the *code*, not the data. Running CHANDRABHAR-2 against
Chandrayaan-2 data does not change, waive, or relicense that data's own terms, and does not grant
the CHANDRABHAR-2 project or its users any ownership interest in Chandrayaan-2 mission products.

## Citation requirement

When publishing or presenting results derived from Chandrayaan-2 data (including results
produced by CHANDRABHAR-2), cite Chandrayaan-2/ISRO/ISSDC as required by the PRADAN archive's own
citation/acknowledgement policy — check the current policy at the source above, as this project
does not restate it verbatim to avoid presenting stale legal text as current.

## Product identifiers

Any Chandrayaan-2 product IDs referenced in this project's configuration files (e.g.
`configs/chandrayaan2_real.json`) or CLI code identify specific real archive products for
development/testing purposes; they are catalogue references, not data included in this
repository.
