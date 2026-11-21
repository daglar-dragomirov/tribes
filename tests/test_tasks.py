import sqlite3

import dspy
import pytest

from tribes import item_context, tasks
from tribes.tasks import canonical_number, extract_code, extract_sql, math_answer, same_output


def P(answer):
    return dspy.Prediction(answer=answer)


# ---------------------------------------------------------------------- math
@pytest.mark.parametrize("a,b", [
    ("\\boxed{1/2}", "0.5"), ("1,000", "1000"), ("The final answer is 42.", "\\boxed{42}"),
    ("\\frac{6}{4}", "3/2"), ("$-0$", "0"), ("\\dfrac{1}{3}", "\\boxed{\\frac{1}{3}}"), ("3.50", "7/2"),
    ("answer: 12", "12"), ("\\boxed{\\left( 3 \\right)}", "(3)"),
])
def test_math_key_equivalences(a, b):
    k = tasks.math_key()
    assert k(P(a)) == k(P(b)) is not None


@pytest.mark.parametrize("a,b", [("41", "42"), ("1/2", "1/3"), ("x+1", "x-1")])
def test_math_key_distinguishes(a, b):
    k = tasks.math_key()
    assert k(P(a)) != k(P(b))


def test_math_helpers():
    assert canonical_number("1,234.50") == "2469/2"
    assert canonical_number("x") is None and canonical_number("1/0") is None
    assert math_answer("so \\boxed{\\frac{1}{2}} and later \\boxed{7}") == "7"
    assert math_answer("long text " * 10 + " total 17 apples") == "17"
    assert tasks.math_key()(P("")) is None


# ---------------------------------------------------------------------- multiple choice
@pytest.mark.parametrize("text,letter", [
    ("B", "B"), ("(C)", "C"), ("D. Paris", "D"), ("The answer is (A)", "A"), ("answer: b", "B"),
    ("\\boxed{C}", "C"), ("A) because", "A"),
])
def test_choice_key(text, letter):
    assert tasks.choice_key()(P(text)) == letter


def test_choice_key_unreadable_is_none():
    assert tasks.choice_key("ABCD")(P("I am not sure")) is None
    assert tasks.choice_key("ABCD")(P("")) is None


def test_generic_keys():
    assert tasks.set_key()(P("b, a; c")) == tasks.set_key()(P("c\na\nb"))
    assert tasks.json_key()(P('{"b": 1, "a": [1, 2]}')) == tasks.json_key()(P('{"a":[1,2],"b":1}'))
    assert tasks.json_key()(P("not json!")) == "not json"
    assert tasks.exact_key()(P("  Hello   World ")) == "hello world"
    assert tasks.normalized_key()(P("The Answer.")) == "answer"
    assert tasks.normalized_key("answer")(P("A")) == "a"  # an option letter is not an empty answer


# ---------------------------------------------------------------------- SQL
@pytest.fixture
def db(tmp_path):
    path = tmp_path / "shop.sqlite"
    con = sqlite3.connect(path)
    con.executescript("""
        create table items(id integer primary key, name text, price real, city text);
        insert into items(name, price, city) values ('pen', 1.5, 'Oslo'), ('ink', 3.0, 'Oslo'), ('cup', 7.25, 'Rome');
    """)
    con.commit()
    con.close()
    return str(path)


def test_sql_key_is_the_result_set(db):
    t = tasks.sql(lambda inputs: db)
    with item_context({"question": "q"}):
        a = t.answer_key(P("SELECT name FROM items WHERE city = 'Oslo' ORDER BY name"))
        b = t.answer_key(P("```sql\nselect name from items where price < 5;\n```"))
        c = t.answer_key(P("SELECT name FROM items"))
        broken = t.answer_key(P("SELECT nope FROM items"))
    assert a == b and a != c and broken is None


def test_sql_is_read_only_and_checked(db):
    t = tasks.sql(lambda inputs: db)
    assert t.checker({"q": 1}, P("select count(*) from items")) is True
    assert t.checker({"q": 1}, P("select * from missing")) is False
    assert t.checker({"q": 1}, P("delete from items")) is False
    assert t.checker({"q": 1}, P("")) is False
    ex = tasks.SQLiteDB()
    with pytest.raises(PermissionError):
        ex.execute(db, "select 1; drop table items")
    assert ex.execute(db, "select 'drop table items'")[1] == [("drop table items",)]  # a literal is fine
    assert ex.execute(db, "select count(*) from items")[1] == [(3,)]


def test_sql_tool_and_evidence(db):
    t = tasks.sql(lambda inputs: db)
    run_sql = t.tools[0]
    assert run_sql.__name__ == "run_sql" and "query" in run_sql.__annotations__
    with item_context({"question": "q"}):
        out = run_sql("select name, price from items order by price")
        err = run_sql("select * from nowhere")
    assert "pen | 1.5" in out and "(3 rows)" in out
    assert err.startswith("error:")
    ev = t.evidence({"question": "q"}, P("select name from items where city='Paris'"))
    assert "EMPTY" in ev
    assert "fails" in t.evidence({"question": "q"}, P("select x from y"))


def test_sql_timeout(tmp_path):
    path = tmp_path / "t.sqlite"
    sqlite3.connect(path).close()
    ex = tasks.SQLiteDB(timeout=0.2, cache=False)
    slow = "with recursive c(x) as (select 1 union all select x + 1 from c where x < 100000000) select count(*) from c"
    with pytest.raises(TimeoutError):
        ex.execute(str(path), slow)


def test_extract_sql():
    assert extract_sql("Here:\n```sql\nSELECT 1;\n```") == "SELECT 1"
    assert extract_sql("select 2;") == "select 2"


# ---------------------------------------------------------------------- code
SQUARE = "n = int(input())\nprint(n * n)"
SQUARE2 = "```python\nimport sys\nx = int(sys.stdin.read())\nprint(x ** 2)\n```"
DOUBLE = "n = int(input())\nprint(n + n)"


def public_tests(inputs):
    return [("2\n", "4"), ("3\n", "9")]


def test_code_key_is_behaviour_on_the_test_inputs():
    t = tasks.code(public_tests)
    with item_context({"question": "square it"}):
        a, b, c = (t.answer_key(P(x)) for x in (SQUARE, SQUARE2, DOUBLE))
    assert a == b and a != c


def test_code_checker_and_tools():
    t = tasks.code(public_tests)
    assert t.checker({}, P(SQUARE)) is True
    assert t.checker({}, P(DOUBLE)) is False
    assert t.checker({}, P("raise SystemExit(3)")) is False
    names = [f.__name__ for f in t.tools]
    assert names == ["run_public_tests", "run_program"]
    with item_context({"question": "q"}):
        report = t.tools[0](DOUBLE)
        out = t.tools[1](SQUARE, "5\n")
    assert "test 1: PASS" in report and "test 2: FAIL" in report
    assert out.strip() == "25"
    assert "public test 2 FAIL" in t.evidence({}, P(DOUBLE))


def test_code_helpers():
    assert extract_code("text\n```python\nprint(1)\n```\nmore") == "print(1)"
    assert same_output("1.0000001\n2", "1 2") and not same_output("1 2", "1 3") and not same_output("1", "1 2")
    out, err, rc = tasks.run_program("while True: pass", timeout=0.5)
    assert rc is None and err == "timeout"


# ---------------------------------------------------------------------- planning and presets
def test_plan_checker_uses_the_stated_constraints():
    def validate(inputs, answer):
        return all(day in answer for day in inputs["must_include"])
    t = tasks.plan(validate)
    assert t.checker({"must_include": ["Mon", "Tue"]}, P("Mon: a, Tue: b")) is True
    assert t.checker({"must_include": ["Mon", "Tue"]}, P("Mon: a")) is False


def test_presets_registry():
    assert set(tasks.PRESETS) == {"math", "choice", "sql", "code", "plan", "free_text", "doc_set", "tool_qa"}
    t = tasks.math().with_(notes="x")
    assert t.notes == "x" and t.answer_key is not None and t.verify
