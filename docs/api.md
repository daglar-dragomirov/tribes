# API reference

## Tribes

::: tribes.Tribes
    options:
      members:
        - fit
        - forward
        - explain
        - run_batch
        - abatch
        - cost_report
        - save_fit
        - load_fit

::: tribes.Selection

## Task adapters

::: tribes.tasks
    options:
      members:
        - Task
        - math
        - choice
        - sql
        - code
        - plan
        - free_text
        - SQLiteDB

## Verifier

::: tribes.Verifier

::: tribes.VerifierGate

## Selection rules and task switches

::: tribes.pick

::: tribes.contested

::: tribes.do_no_harm

::: tribes.non_inferiority

::: tribes.switch_power

::: tribes.paired_stats

::: tribes.text_key

## Observability and cost

::: tribes.Callback

::: tribes.LoggingCallback

::: tribes.JSONLCallback

::: tribes.Ledger

## Offline replay

::: tribes.replay

## Forms and tools

::: tribes.Assembled

::: tribes.Liquid

::: tribes.run_python

::: tribes.item_tool
