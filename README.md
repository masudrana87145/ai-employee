# ai-employee

Python greeting CLI and a small HTTP API.

## Source file location

| What | Path |
| --- | --- |
| Local project root | `C:\Users\khand\OneDrive\Desktop\ai-employee` |
| CLI source | `hello.py` |
| Arithmetic source | `arith.py` |
| API source | `api.py` |
| Country time API | `country_time_api.py`, `country_zones.py` |
| Tests | `tests\test_hello.py`, `tests\test_arith.py`, `tests\test_api.py`, `tests\test_country_time_api.py` |
| Skill that drove this work | `C:\Users\khand\.cursor\skills\ai-employee-python-developer\SKILL.md` |

## Requirements

- Python 3.12 or newer

## CLI usage

```powershell
python hello.py Rana
```

Expected output:

```text
Hello Rana
```

## Arithmetic CLI

Call `add`, `mult`, or `sub`, then two integers (`arg1` and `arg2`):

```powershell
python arith.py add 5 4
python arith.py mult 5 4
python arith.py sub 5 4
python arith.py div 5 4
```

Expected output:

```text
9
20
1
1.25
```

`sub` subtracts `arg2` from `arg1`. `div` divides `arg1` by `arg2`. Division by zero prints an error and exits with code 2. The function name may be any letter case. Any other name prints an error that lists `add`, `mult`, `sub`, and `div` with their purposes, and exits with code 2.

The same operations are available in Python:

```python
from arith import calculate

calculate("add", 5, 4)  # 9
```

## API

Install the project, including test tools:

```powershell
python -m pip install -e ".[dev]"
```

Start the API:

```powershell
python api.py
```

The server listens on `http://127.0.0.1:8000`. Interactive docs are at `/docs`.

### List arithmetic operations

`GET /`

```json
{
  "operations": [
    {"task": "add", "purpose": "Add two numbers"},
    {"task": "mult", "purpose": "Multiply two numbers"},
    {"task": "sub", "purpose": "Subtract the second number from the first"},
    {"task": "div", "purpose": "Divide the first number by the second"}
  ],
  "sample_payload": {"task": "add", "parm1": 5, "parm2": 4}
}
```

`sample_payload` is a valid body for `POST /task`.

### Greet a query value

`GET /hi?name=Masud`

```json
{"message": "Hi, Masud"}
```

A blank name returns HTTP 422.

### Run an integer task

`POST /task` with a JSON body. `task` may be any letter case. `parm1` and `parm2` must be integers.

```json
{"task": "add", "parm1": 5, "parm2": 4}
```

```json
{"message": "Sum of 5 and 4 is 9"}
```

| Task | Purpose | Result message |
| --- | --- | --- |
| `add` | Add two numbers | `Sum of 5 and 4 is 9` |
| `mult` | Multiply two numbers | `Product of 5 and 4 is 20` |
| `sub` | Subtract the second number from the first | `Difference of 5 and 4 is 1` |
| `div` | Divide the first number by the second | `Quotient of 5 and 4 is 1.25` |

Any other task returns HTTP 400 with the valid tasks and their purposes:

```json
{
  "error": "Unsupported task 'divide'.",
  "valid_tasks": [
    {"task": "add", "purpose": "Add two numbers"},
    {"task": "mult", "purpose": "Multiply two numbers"},
    {"task": "sub", "purpose": "Subtract the second number from the first"},
    {"task": "div", "purpose": "Divide the first number by the second"}
  ]
}
```

`GET /health` and `GET /ready` report that the process is up.

## Country time API

Start it on port 8001:

```powershell
python country_time_api.py
```

`GET /time?country=Japan` returns the current civil time. `country` may be an English name or an ISO code (`JP`, `JPN`). Letter case and extra spaces are ignored. Common names such as `USA`, `UK`, and `South Korea` are accepted. A response looks like this:

```json
{
  "country": "Japan",
  "country_code": "JP",
  "timezones": [
    {
      "timezone": "Asia/Tokyo",
      "region": "",
      "local_time": "2026-10-19T05:03:00+09:00",
      "utc_offset": "+09:00",
      "abbreviation": "JST"
    }
  ]
}
```

A country with more than one civil time zone returns each zone. `region` is the IANA note for that zone, and it is empty when the country has only one. An unknown country returns HTTP 404. A blank `country` returns HTTP 422.

`GET /health` and `GET /ready` report that this process is up. The systemd unit is `deploy/country-time-api.service`, listening on `0.0.0.0` port 8001.

Bouvet Island (`BV`) and Heard Island and McDonald Islands (`HM`) are not included. The IANA time zone database has no civil time zone for those uninhabited territories.

## Tests

```powershell
python -m unittest discover -s tests -v
```
