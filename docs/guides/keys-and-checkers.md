# Answer keys and checkers

Two optional callables make the vote and the filter sharper. Neither may read the label.

## `answer_key(prediction) -> hashable | None`

Decides when two forms "give the same answer". The default lower-cases the output, removes punctuation and articles, and
collapses whitespace. Pass your own when the task has a canonical form:

=== "Math"

    ```python
    import re

    def math_key(pred):
        s = str(pred.answer)
        m = re.findall(r"\\boxed\{(.*)\}", s)
        s = (m[-1] if m else s).replace("$", "").replace(" ", "").rstrip(".")
        return str(int(s)) if re.fullmatch(r"-?\d+", s) else s.lower()
    ```

=== "Multiple choice"

    ```python
    def letter_key(pred):
        m = re.match(r"^\W*([ABCD])\b", str(pred.answer).strip())
        return m.group(1) if m else None
    ```

=== "Text-to-SQL"

    ```python
    def sql_key(pred):
        rows = run_readonly(pred.answer)          # your executor; None if the query fails
        return None if rows is None else hash(frozenset(map(tuple, rows)))
    ```

Returning `None` means "no usable answer": the form is treated like a broken output.

## `checker(inputs, prediction) -> bool | None`

A deterministic test that needs no labels. Forms that fail it are dropped before the vote; if every form fails, all are
kept. Return `None` when the check does not apply.

```python
def public_tests(inputs, pred):
    return run_public_tests(inputs["question"], pred.answer)   # True / False
```

Good checkers: the statement's public unit tests for code, "the SQL query runs and returns rows", a validator of the
constraints stated in a planning problem. In the research evaluation they added about +0.3 pp on top of the vote; the
layer works without them.

## Ready-made adapters

`tribes.tasks` bundles a key, a checker, tools and verifier evidence per task type; pass one as `task=`:

| adapter | answers agree when | checker | tools |
|---|---|---|---|
| `math()` | the final number or expression is equal by value (`\boxed{}`, fractions, `1,000`) | - | `run_python` |
| `choice("ABCD")` | the option letter is equal | - | - |
| `sql(db_for)` | the queries return the same rows | the query runs | read-only `run_sql` on the item's database |
| `code(tests_for)` | the programs print the same on the public-test inputs | passes the public tests | `run_public_tests`, `run_program` |
| `plan(validate)` | normalised text | your validator of the stated constraints | - |
| `tool_qa()` | normalised text | an abstention is not an answer | - |
| `doc_set()` | (merged, not voted) | - | - |

`db_for(inputs)` and `tests_for(inputs)` read the current item; tools that need it use `tribes.item_tool`.

## Set-valued outputs: merge instead of select

When the output is a set of items scored by recall (retrieved documents, cited sources, tags), choosing one form's set
throws away what the others found. `tasks.doc_set()` merges them: every item gets the number of forms that returned it,
items are ordered by that count, and the first *k* are kept, where *k* is the size of the program's own output (its
budget). On HoVer this beat taking the reviewer's set by about +6 pp on development data for each of GEPA, MIPROv2 and
SIMBA.

## Contested inputs: the verifier

`Tribes(program, verifier=True)` adds a verifier for inputs where no two forms agree. It must run one check whose
result differs between the candidates (substituting an answer back, code on edge-case inputs, an auxiliary SQL query),
and code - not the model - accepts a switch only if the quoted evidence matches a tool observation; a switch needs two of
three votes. `fit` enables it per task only if, on the selection data, it gains more than 0.5 pp and wins at least two
more items than it loses.
