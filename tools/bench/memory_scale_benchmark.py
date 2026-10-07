from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import platform
import statistics
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "orion_v3"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from modules.canonical_memory_retrieval_foundation import (  # noqa: E402
    CanonicalMemoryRetrievalFoundation,
    MAX_CANDIDATES,
)
from modules.memory_candidate_queue import MAX_CANDIDATES as CANDIDATE_QUEUE_MAX  # noqa: E402


def _sha256_text(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _working_set_mb() -> float | None:
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(counters)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(
                handle,
                ctypes.byref(counters),
                counters.cb,
            )
            if ok:
                return round(counters.WorkingSetSize / (1024 * 1024), 3)
        except Exception:
            return None
    try:
        import resource
        value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if sys.platform == "darwin":
            value /= 1024 * 1024
        else:
            value /= 1024
        return round(value, 3)
    except Exception:
        return None


@dataclass
class Fixture:
    memories: list[dict[str, Any]]
    candidates: list[dict[str, Any]]
    current_ids: list[str]
    current_by_marker: dict[str, str]
    project_by_marker: dict[str, str]
    historical_pairs: list[tuple[str, str, str]]


class BenchReview:
    def __init__(self, memories: list[dict[str, Any]]):
        self.memories = memories

    def list_canonical(self, include_revoked=False):
        active = [x for x in self.memories if bool(x.get("active"))]
        return {
            "all_memories": self.memories,
            "memories": active,
            "count": len(active),
            "revoked_count": len(self.memories) - len(active),
        }


class BenchCandidates:
    def __init__(self, candidates: list[dict[str, Any]]):
        self.candidates = candidates

    def list(self):
        return {
            "candidates": self.candidates,
            "count": len(self.candidates),
        }


def build_fixture(scale: int) -> Fixture:
    scale = max(100, int(scale))
    historical_count = max(1, int(scale * 0.05))
    current_count = scale - historical_count

    memories: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    current_ids: list[str] = []
    current_by_marker: dict[str, str] = {}
    project_by_marker: dict[str, str] = {}

    def add_row(
        *,
        memory_id: str,
        candidate_id: str,
        content: str,
        project_id: str,
        created_at_ms: int,
    ) -> None:
        content_hash = _sha256_text(content)
        memories.append({
            "memory_id": memory_id,
            "schema": "orion.canonical-memory/1",
            "candidate_id": candidate_id,
            "content": content,
            "content_sha256": content_hash,
            "owner_scope": "owner:primary",
            "project_id": project_id,
            "classification": "conversation_recall",
            "trust_origin": "user",
            "trust_tier": "owner_message_unverified",
            "source_ref": f"bench:{candidate_id}",
            "promoted_decision_id": f"decision-{memory_id}",
            "promoted_event_hash": _sha256_text("event:" + memory_id),
            "created_at_ms": created_at_ms,
            "status": "active",
            "active": True,
            "canonical": True,
            "authority": "context_only",
        })
        candidates.append({
            "candidate_id": candidate_id,
            "content": content,
            "content_sha256": content_hash,
            "source_conversation_id": f"conv-{candidate_id}",
            "source_message_id": f"msg-{candidate_id}",
            "source_role": "user",
            "project_id": project_id,
            "owner_scope": "owner:primary",
            "trust_tier": "owner_message_unverified",
        })

    for i in range(current_count):
        marker = f"z{i:07d}"
        project = f"p{i % 3}"
        memory_id = f"cm-current-{i:07d}"
        candidate_id = f"cand-current-{i:07d}"
        content = (
            f"Benchmark owner memory {marker} topic t{i % 200:03d} "
            f"for {project} has value v{i % 11}."
        )
        add_row(
            memory_id=memory_id,
            candidate_id=candidate_id,
            content=content,
            project_id=project,
            created_at_ms=2_000_000 + i,
        )
        current_ids.append(memory_id)
        current_by_marker[marker] = memory_id
        project_by_marker[marker] = project

    historical_pairs: list[tuple[str, str, str]] = []
    for j in range(historical_count):
        current_index = (j * 17) % current_count
        marker = f"z{current_index:07d}"
        project = project_by_marker[marker]
        prior_id = f"cm-historical-{j:07d}"
        prior_candidate = f"cand-historical-{j:07d}"
        content = (
            f"Benchmark owner memory {marker} topic t{current_index % 200:03d} "
            f"for {project} had historical value old{j % 7}."
        )
        add_row(
            memory_id=prior_id,
            candidate_id=prior_candidate,
            content=content,
            project_id=project,
            created_at_ms=1_000_000 + j,
        )
        historical_pairs.append(
            (prior_id, current_by_marker[marker], marker)
        )

    return Fixture(
        memories=memories,
        candidates=candidates,
        current_ids=current_ids,
        current_by_marker=current_by_marker,
        project_by_marker=project_by_marker,
        historical_pairs=historical_pairs,
    )


def seed_supersessions(
    foundation: CanonicalMemoryRetrievalFoundation,
    fixture: Fixture,
) -> None:
    import sqlite3

    rows = []
    prev = ""
    for idx, (prior_id, replacement_id, marker) in enumerate(
        fixture.historical_pairs,
        start=1,
    ):
        prior = next(x for x in fixture.memories if x["memory_id"] == prior_id)
        replacement = next(
            x for x in fixture.memories
            if x["memory_id"] == replacement_id
        )
        event_hash = _sha256_text(f"sup:{idx}:{prior_id}:{replacement_id}:{prev}")
        rows.append((
            idx,
            f"sup-{idx:07d}",
            "orion.canonical-memory-supersession/1",
            prior_id,
            replacement_id,
            prior["content_sha256"],
            replacement["content_sha256"],
            "owner:primary",
            prior["project_id"],
            "bench",
            "bench-ticket",
            "benchmark_fixture",
            3_000_000 + idx,
            prev,
            event_hash,
        ))
        prev = event_hash

    if not rows:
        return

    with sqlite3.connect(foundation.supersession_path) as con:
        con.executemany(
            """
            INSERT INTO supersession_events(
                event_index,supersession_id,schema,prior_memory_id,
                replacement_memory_id,prior_content_sha256,
                replacement_content_sha256,owner_scope,project_id,
                actor_fingerprint,review_ticket_sha256,reason,
                created_at_ms,prev_event_hash,event_hash
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )
        con.commit()


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * p
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return ordered[low]
    frac = pos - low
    return ordered[low] * (1.0 - frac) + ordered[high] * frac


def run_case(scale: int, queries: int = 60) -> dict[str, Any]:
    fixture = build_fixture(scale)
    rss_before = _working_set_mb()

    with tempfile.TemporaryDirectory(prefix=f"orion-memory-bench-{scale}-") as td:
        foundation = CanonicalMemoryRetrievalFoundation(
            BenchReview(fixture.memories),
            pathlib.Path(td) / "supersession.sqlite3",
            BenchCandidates(fixture.candidates),
        )
        seed_supersessions(foundation, fixture)

        markers = sorted(fixture.current_by_marker)
        sample_count = max(1, min(int(queries), len(markers)))
        step = max(1, len(markers) // sample_count)
        sampled = markers[::step][:sample_count]

        cold_started = time.perf_counter()
        first_marker = sampled[0]
        cold = foundation.retrieve(
            first_marker,
            project_id=fixture.project_by_marker[first_marker],
            limit=6,
        )
        cold_wall_ms = (time.perf_counter() - cold_started) * 1000.0

        latencies: list[float] = []
        top1_hits = 0
        top5_hits = 0
        candidate_counts: list[int] = []
        scope_ok = True

        for marker in sampled:
            project = fixture.project_by_marker[marker]
            expected = fixture.current_by_marker[marker]
            started = time.perf_counter()
            result = foundation.retrieve(
                marker,
                project_id=project,
                limit=6,
            )
            latencies.append((time.perf_counter() - started) * 1000.0)
            ids = [str(x.get("memory_id") or "") for x in result["items"]]
            if ids and ids[0] == expected:
                top1_hits += 1
            if expected in ids[:5]:
                top5_hits += 1
            candidate_counts.append(
                int(result["trace"].get("candidate_count") or 0)
            )
            if any(
                str(x.get("project_id") or "") != project
                for x in result["items"]
            ):
                scope_ok = False

        history_ok = True
        history_checks = min(20, len(fixture.historical_pairs))
        for prior_id, replacement_id, marker in fixture.historical_pairs[:history_checks]:
            project = fixture.project_by_marker[marker]
            l1 = foundation.retrieve(
                marker,
                project_id=project,
                limit=12,
                include_historical=False,
            )
            l2 = foundation.retrieve(
                marker,
                project_id=project,
                limit=12,
                include_historical=True,
            )
            l1_ids = {str(x.get("memory_id") or "") for x in l1["items"]}
            l2_status = {
                str(x.get("memory_id") or ""): str(x.get("status") or "")
                for x in l2["items"]
            }
            if (
                prior_id in l1_ids
                or replacement_id not in l1_ids
                or l2_status.get(prior_id) != "historical"
                or replacement_id not in l2_status
            ):
                history_ok = False
                break

        rss_after = _working_set_mb()

    return {
        "scale": scale,
        "synthetic_canonical_records": len(fixture.memories),
        "queries": sample_count,
        "production_candidate_queue_cap": CANDIDATE_QUEUE_MAX,
        "production_ingest_scale_supported": scale <= CANDIDATE_QUEUE_MAX,
        "note": (
            "At scales above the current candidate-queue cap this measures the "
            "frozen canonical retrieval algorithm with synthetic public projections; "
            "it does not claim current production ingestion supports that scale."
        ),
        "latency_ms": {
            "cold_wall": round(cold_wall_ms, 3),
            "warm_p50": round(percentile(latencies, 0.50), 3),
            "warm_p99": round(percentile(latencies, 0.99), 3),
            "mean": round(statistics.fmean(latencies), 3) if latencies else 0.0,
            "foundation_reported_cold": float(
                cold.get("trace", {}).get("elapsed_ms") or 0.0
            ),
        },
        "ranking": {
            "top1_accuracy": round(top1_hits / sample_count, 4),
            "top5_recall": round(top5_hits / sample_count, 4),
        },
        "scope_isolation": scope_ok,
        "current_historical_correctness": history_ok,
        "candidate_count": {
            "mean": round(statistics.fmean(candidate_counts), 3)
            if candidate_counts else 0.0,
            "max": max(candidate_counts) if candidate_counts else 0,
            "retrieval_candidate_cap": MAX_CANDIDATES,
        },
        "process_working_set_mb": {
            "before": rss_before,
            "after": rss_after,
            "delta": (
                round(rss_after - rss_before, 3)
                if rss_before is not None and rss_after is not None
                else None
            ),
        },
    }


def threshold_verdict(case: dict[str, Any]) -> dict[str, Any]:
    scale = int(case["scale"])
    thresholds = {
        1000: {"cold": 400, "p50": 60, "p99": 200, "top1": 0.95, "top5": 0.99},
        10000: {"cold": 1500, "p50": 200, "p99": 800, "top1": 0.90, "top5": 0.95},
        100000: {"cold": 6000, "p50": 800, "p99": 3000, "top1": 0.85, "top5": 0.90},
    }
    nearest = min(thresholds, key=lambda n: abs(n - scale))
    t = thresholds[nearest]
    checks = {
        "cold_latency": case["latency_ms"]["cold_wall"] <= t["cold"],
        "warm_p50": case["latency_ms"]["warm_p50"] <= t["p50"],
        "warm_p99": case["latency_ms"]["warm_p99"] <= t["p99"],
        "top1_accuracy": case["ranking"]["top1_accuracy"] >= t["top1"],
        "top5_recall": case["ranking"]["top5_recall"] >= t["top5"],
        "scope_isolation": bool(case["scope_isolation"]),
        "current_historical_correctness": bool(
            case["current_historical_correctness"]
        ),
    }
    return {
        "threshold_profile": nearest,
        "checks": checks,
        "pass": all(checks.values()),
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# ORION Memory Scale Benchmark",
        "",
        f"Generated: {report['generated_utc']}",
        f"Hardware: {report['hardware']}",
        "",
        "| Scale | Cold ms | Warm p50 | Warm p99 | Top-1 | Top-5 | Scope | L1/L2 | Verdict |",
        "|---:|---:|---:|---:|---:|---:|:---:|:---:|:---:|",
    ]
    for case in report["cases"]:
        v = case["verdict"]
        lines.append(
            f"| {case['scale']:,} | {case['latency_ms']['cold_wall']:.1f} | "
            f"{case['latency_ms']['warm_p50']:.1f} | {case['latency_ms']['warm_p99']:.1f} | "
            f"{case['ranking']['top1_accuracy']:.3f} | {case['ranking']['top5_recall']:.3f} | "
            f"{'PASS' if case['scope_isolation'] else 'FAIL'} | "
            f"{'PASS' if case['current_historical_correctness'] else 'FAIL'} | "
            f"{'PASS' if v['pass'] else 'FAIL'} |"
        )
    lines += [
        "",
        "## Important production constraint",
        "",
        f"Current Memory V1 candidate queue hard cap: **{CANDIDATE_QUEUE_MAX}**.",
        "Runs above that scale are retrieval-core experiments using synthetic public projections; "
        "they are intentionally not claims that the current V1 ingestion path supports that many memories.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--scales",
        default="1000,10000,100000",
        help="Comma-separated canonical record counts.",
    )
    ap.add_argument("--queries", type=int, default=60)
    ap.add_argument("--output-dir", default="")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    scales = [int(x.strip()) for x in args.scales.split(",") if x.strip()]
    if args.smoke:
        scales = [250]
        args.queries = 8

    cases = []
    for scale in scales:
        case = run_case(scale, queries=args.queries)
        case["verdict"] = threshold_verdict(case)
        cases.append(case)

    report = {
        "schema": "orion.memory-scale-benchmark/1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware": (
            f"{platform.system()} {platform.release()} | "
            f"{platform.machine()} | Python {platform.python_version()}"
        ),
        "cases": cases,
        "frozen_memory_v1_modified": False,
        "production_runtime_loaded": False,
    }

    if args.output_dir:
        out = pathlib.Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        json_path = out / f"memory_bench_{stamp}.json"
        md_path = out / f"memory_bench_{stamp}.md"
        json_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        md_path.write_text(markdown_report(report), encoding="utf-8")
        print(f"JSON_REPORT> {json_path}")
        print(f"MARKDOWN_REPORT> {md_path}")

    print(json.dumps(report, ensure_ascii=False))
    if args.smoke:
        case = cases[0]
        if not (
            case["scope_isolation"]
            and case["current_historical_correctness"]
            and case["ranking"]["top1_accuracy"] >= 0.95
            and case["ranking"]["top5_recall"] >= 0.99
        ):
            return 1
        print("ORION_MEMORY_SCALE_BENCH_SMOKE> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
