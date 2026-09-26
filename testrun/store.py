class Store:
    def __init__(self) -> None:
        self._runs: dict[int, dict] = {}
        self._next_id = 1

    def reset(self) -> None:
        self._runs.clear()
        self._next_id = 1

    def create_run(self, name: str, tests: list[str]) -> dict:
        if name == "":
            raise ValueError("name is required")
        if len(tests) == 0:
            raise ValueError("at least one test is required")

        run_id = self._next_id
        self._next_id += 1
        self._runs[run_id] = {
            "id": run_id,
            "name": name,
            "tests": list(tests),
            "results": {},
        }
        return {
            "id": run_id,
            "name": name,
            "tests": list(tests),
            "status": "queued",
        }

    def add_result(self, run_id: int, test: str, status: str, duration_ms: int) -> dict:
        run = self._runs.get(run_id)
        if run is None:
            raise KeyError("run not found")
        if status.lower() not in ("pass", "fail", "skip"):
            raise ValueError("status must be pass, fail, or skip")
        if test not in run["tests"]:
            raise ValueError("unknown test")
        if not isinstance(duration_ms, int) or isinstance(duration_ms, bool):
            raise ValueError("duration_ms must be an integer")

        run["results"][test] = {"status": status, "duration_ms": duration_ms}
        return {
            "id": run_id,
            "test": test,
            "status": status,
            "duration_ms": duration_ms,
        }

    def summary(self, run_id: int) -> dict:
        run = self._runs.get(run_id)
        if run is None:
            return {
                "id": run_id,
                "name": None,
                "status": "queued",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "pass_rate": 0.0,
                "duration_ms": 0,
            }

        results = run["results"]
        passed = sum(1 for item in results.values() if item["status"] == "pass")
        failed = sum(1 for item in results.values() if item["status"] == "fail")
        skipped = sum(1 for item in results.values() if item["status"] == "skip")

        if not results:
            status = "queued"
        elif failed:
            status = "failed"
        elif passed:
            status = "passed"
        elif len(results) < len(run["tests"]):
            status = "running"
        else:
            status = "passed"

        if passed + failed == 0:
            pass_rate = 0.0
        else:
            pass_rate = passed / (passed + failed)

        return {
            "id": run["id"],
            "name": run["name"],
            "status": status,
            "total": len(run["tests"]),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": pass_rate,
            "duration_ms": sum(item["duration_ms"] for item in results.values()),
        }


store = Store()
