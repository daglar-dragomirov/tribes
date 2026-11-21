# Choosing a mode

| | `lite` | `full` |
|---|---|---|
| runs per input | reviewer (whose draft is one program run) | program + reviewer; agent only on disagreement |
| inference cost | about 2.6× the program | about 4.6× the program |
| development gain (36 cells) | +8.9 pp | +9.5 pp |
| sealed-test gain (15 cells) | +7.1 pp | not measured |

On fresh items (TEST-B, 15 cells, TRIBES 1.1) `full` beat `lite` by +2.0 pp [+1.2, +2.7] on the same forms. The
per-task choice of mode (fixed on selection data) gained +4.7 pp over the programs, and `full` everywhere plus the verifier
+5.2 pp.

Use **`lite`** when cost matters or outputs are free text (summaries, code, document sets), where two forms almost never
agree word for word and the vote has nothing to do.

Use **`full`** when answers are short and comparable (numbers, labels, option letters, SQL results): there the vote of
independent forms adds the most.

Either way, `fit` decides per task whether the layer is used at all. Where it is switched off, the cost is the program's.
