# Laser 2D-to-3D Assembly — Review Rubric

> Documentation class: PUBLIC_DOMAIN
Version: 0.1.0 · Proposed release policy for cut drawings; construction remains requester responsibility.

| Criterion | Weight | Full-credit evidence |
| --- | ---: | --- |
| Session intake and material triple | 25 | Material/thickness/kerf/clearance specified per session |
| Source branch and proxy honesty | 20 | from_3d hashed or from_photo labeled proxy with capped release |
| Slot/slice engineering | 20 | Slot ledger or slice-step + alignment verified |
| Closed profiles and nesting | 15 | All CUT closed, bridges recorded, layout fits sheet |
| DXF/PDF usability and recovery | 20 | Reopened DXF + labeled assembly guide + failure evidence |

Rate 0–4: 0 absent/failed; 1 major gaps; 2 partial; 3 meets scope; 4 complete including adverse-case evidence. Score = sum(weight × rating/4).

Release requires ≥90/100 and all hard gates: material triple resolved for requested release; source hashed or proxy labeled; slot/slice math recorded; closed CUT profiles; nesting fits sheet; DXF reopened with units verified; part labels/BOM/notes present; sealed hashes; recovery verified. A visually plausible layout cannot override a failed measurement gate. Photo-derived joints need approval or test-cut before fabrication_candidate.
