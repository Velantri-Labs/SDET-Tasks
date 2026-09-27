class Store:
    def __init__(self) -> None:
        self._runs: dict[int, dict] = {}
        self._next_id = 1

    def reset(self) -> None:
        self._runs.clear()
        self._next_id = 1

    def create_run(self, name: str, tests: list[str]) -> dict:
        name = name.strip()
        if not (1 <= len(name) <= 40):
            raise ValueError("name must be 1-40 characters")

        if not (1 <= len(tests) <= 20):
            raise ValueError("tests must contain 1-20 items")

        trimmed_tests: list[str] = []
        for test in tests:
            trimmed = test.strip()
            if not (1 <= len(trimmed) <= 60):
                raise ValueError("each test name must be 1-60 characters")
            trimmed_tests.append(trimmed)

        if len(set(trimmed_tests)) != len(trimmed_tests):
            raise ValueError("test names must be unique")

        run_id = self._next_id
        self._next_id += 1
        self._runs[run_id] = {
            "id": run_id,
            "name": name,
            "tests": list(trimmed_tests),
            "results": {},
        }
        return {
            "id": run_id,
            "name": name,
            "tests": list(trimmed_tests),
            "status": "queued",
        }

    def add_result(self, run_id: int, test: str, status: str, duration_ms: int) -> dict:
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError("run not found")

        test = test.strip()
        if test not in run["tests"]:
            raise ValueError("unknown test")

        status = status.strip().lower()
        if status not in ("pass", "fail", "skip"):
            raise ValueError("status must be pass, fail, or skip")

        if not isinstance(duration_ms, int) or isinstance(duration_ms, bool) or duration_ms < 0:
            raise ValueError("duration_ms must be an integer >= 0")

        if test in run["results"]:
            raise ValueError("a result already exists for this test")

        run["results"][test] = {"status": status, "duration_ms": duration_ms}
        return {
            "id": run_id,
            "test": test,
            "status": status,
            "duration_ms": duration_ms,
        }

    @staticmethod
    def _counts(run: dict) -> tuple[int, int, int]:
        results = run["results"]
        passed = sum(1 for item in results.values() if item["status"] == "pass")
        failed = sum(1 for item in results.values() if item["status"] == "fail")
        skipped = sum(1 for item in results.values() if item["status"] == "skip")
        return passed, failed, skipped

    @staticmethod
    def _status(run: dict, failed: int) -> str:
        results = run["results"]
        if not results:
            return "queued"
        if failed:
            return "failed"
        if len(results) < len(run["tests"]):
            return "running"
        return "passed"

    @staticmethod
    def _pass_rate(passed: int, failed: int) -> float:
        if passed + failed == 0:
            return 0.0
        return passed / (passed + failed)

    def summary(self, run_id: int) -> dict:
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError("run not found")

        passed, failed, skipped = self._counts(run)
        status = self._status(run, failed)
        pass_rate = self._pass_rate(passed, failed)

        return {
            "id": run["id"],
            "name": run["name"],
            "status": status,
            "total": len(run["tests"]),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": pass_rate,
            "duration_ms": sum(item["duration_ms"] for item in run["results"].values()),
        }

    def list_runs(self) -> list[dict]:
        rows = []
        for run in self._runs.values():
            passed, failed, _skipped = self._counts(run)
            rows.append({
                "id": run["id"],
                "name": run["name"],
                "status": self._status(run, failed),
                "total": len(run["tests"]),
                "pass_rate": self._pass_rate(passed, failed),
                "tests": list(run["tests"]),
            })
        rows.sort(key=lambda row: row["id"], reverse=True)
        return rows


store = Store()
