# CareFlow dashboard kit: layout guide

Canvas: 1280 x 720 (Power BI default 16:9). Colors: navy #0B2545, teal #13A89E (good / ideal),
coral #F25F5C (problem / bottleneck), amber #FFB703 (warning), blue #5C80BC.
Rule: **coral always means "the problem", teal always means "the ideal / the fix".**

## How to apply
1. **Theme:** View > Themes > Browse for themes > CareFlow_theme.json
2. **Background (per page):** click an empty area of the page > Format page > Canvas background >
   Image > Browse > pick that page's PNG > Image fit: Fit > Transparency: 0%
3. **Position a visual exactly:** select it > Format visual > General > Properties >
   Size (Width, Height) and Position (X, Y), using the tables below.

## Page 1: Overview ("Where do ER patients lose time?")
| Slot | X | Y | W | H |
|---|---|---|---|---|
| Header title text box (white text) | 24 | 12 | 700 | 44 |
| Page navigator (header, right side) | 760 | 14 | 496 | 40 |

| KPI card 1-5 (x = 24, 274, 524, 774, 1024) | x | 84 | 232 | 86 |
| Bottleneck bar chart | 24 | 188 | 600 | 262 |
| Patient journey flow | 642 | 188 | 614 | 262 |
| Donut: followed ideal path | 24 | 468 | 398 | 228 |
| Journey variants | 440 | 468 | 398 | 228 |
| "So what?" insight text box | 856 | 468 | 400 | 228 |

## Page 2: Bottlenecks ("Is it the queue or the work?")
| Slot | X | Y | W | H |
|---|---|---|---|---|
| Wait vs service time by activity | 24 | 90 | 760 | 330 |
| X-ray wait by severity | 802 | 90 | 454 | 330 |
| Hand-offs table | 24 | 438 | 1232 | 258 |

## Page 3: Journeys ("How do patients really move?")
| Slot | X | Y | W | H |
|---|---|---|---|---|
| Process map / flow | 24 | 90 | 780 | 606 |
| Variants table | 822 | 90 | 434 | 300 |
| Insight text box | 822 | 408 | 434 | 288 |

## Page 4: Deviations ("Who leaves the ideal path, and what does it cost?")
| Slot | X | Y | W | H |
|---|---|---|---|---|
| KPI cards (x = 24, 440, 856) | x | 90 | 400 | 90 |
| Donut compliant vs not | 24 | 198 | 400 | 498 |
| Detour by severity | 440 | 198 | 400 | 498 |
| Deviation table + insight | 856 | 198 | 400 | 498 |

## Page 5: What-if ("What would actually fix it?")
| Slot | X | Y | W | H |
|---|---|---|---|---|
| Average stay by scenario | 24 | 90 | 606 | 380 |
| X-ray wait by scenario | 648 | 90 | 608 | 380 |
| Takeaway and recommendation text | 24 | 488 | 1232 | 208 |

Header text: bold white Segoe UI Semibold 22 pt. Visual titles: use plain-English questions,
not field names (e.g. "Which step makes patients wait the longest?").
