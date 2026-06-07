"""Tests for migrations/author.py — JSON-driven problem authoring."""
import json

import pytest

from migrations.author import (
    _to_candidate,
    append_to_registry,
    load_candidates,
    validate_metadata,
)

# ── field translation (NewProblem field names -> build() candidate) ──────────────

class TestToCandidate:
    def test_maps_sympy_and_hint_fields(self):
        c = _to_candidate({
            "integrand": "x**2",
            "lower": "sp.Integer(0)",
            "upper": "sp.Integer(1)",
            "progressive_hints": ["h"],
            "topic": "T",
            "difficulty": "easy",
            "integral_type": "definite",
        })
        assert c["isrc"] == "x**2"
        assert c["lsrc"] == "sp.Integer(0)"
        assert c["usrc"] == "sp.Integer(1)"
        assert c["hints"] == ["h"]
        # passthrough fields keep their names
        assert c["topic"] == "T"
        assert c["integral_type"] == "definite"

    def test_passthrough_fields_unchanged(self):
        c = _to_candidate({
            "integrand": "x", "solution": "x^2/2 + C", "problem": r"\int x dx",
            "topic": "T", "difficulty": "easy", "progressive_hints": ["h"],
            "trusted": True,
        })
        assert c["solution"] == "x^2/2 + C"
        assert c["problem"] == r"\int x dx"
        assert c["trusted"] is True

    def test_requires_integrand(self):
        with pytest.raises(ValueError, match="integrand"):
            _to_candidate({"topic": "T", "difficulty": "easy", "progressive_hints": ["h"]})

    def test_rejects_unknown_field(self):
        with pytest.raises(ValueError, match="unknown field"):
            _to_candidate({"integrand": "x", "bogus": 1})


# ── load_candidates ─────────────────────────────────────────────────────────────

class TestLoadCandidates:
    def test_single_object_wrapped_in_list(self, tmp_path):
        p = tmp_path / "one.json"
        p.write_text(json.dumps({
            "integrand": "x", "topic": "T", "difficulty": "easy",
            "progressive_hints": ["h"],
        }))
        out = load_candidates(str(p))
        assert isinstance(out, list) and len(out) == 1
        assert out[0]["isrc"] == "x"

    def test_list_of_objects(self, tmp_path):
        p = tmp_path / "many.json"
        p.write_text(json.dumps([
            {"integrand": "x", "topic": "T", "difficulty": "easy", "progressive_hints": ["h"]},
            {"integrand": "x**2", "topic": "T", "difficulty": "easy", "progressive_hints": ["h"]},
        ]))
        assert len(load_candidates(str(p))) == 2

    def test_rejects_non_object_top_level(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(ValueError):
            load_candidates(str(p))


# ── validate_metadata ───────────────────────────────────────────────────────────

class TestValidateMetadata:
    def _candidate(self, **kw):
        base = {
            "isrc": "x**2", "problem": r"\int x^2 dx", "solution": r"\frac{x^3}{3} + C",
            "topic": "Power", "difficulty": "easy", "hints": ["power rule"],
        }
        base.update(kw)
        return base

    def test_valid_returns_none(self):
        assert validate_metadata(self._candidate()) is None

    def test_bad_difficulty_returns_message(self):
        msg = validate_metadata(self._candidate(difficulty="extreme"))
        assert msg and "difficulty" in msg

    def test_definite_missing_bounds_returns_message(self):
        msg = validate_metadata(self._candidate(integral_type="definite"))
        assert msg and "bound" in msg.lower()


# ── append_to_registry ──────────────────────────────────────────────────────────

class TestAppendToRegistry:
    def _fake_registry(self, tmp_path):
        p = tmp_path / "registry.py"
        p.write_text(
            "PROBLEMS = [\n"
            "    NewProblem(problem='a', solution='b'),\n"
            "]\n"
        )
        return p

    def test_inserts_before_closing_bracket(self, tmp_path):
        p = self._fake_registry(tmp_path)
        append_to_registry(["    NewProblem(problem='c', solution='d'),"], path=str(p))
        text = p.read_text()
        assert "problem='c'" in text
        # the new entry comes before the final close, file still ends with ]
        assert text.rstrip().endswith("]")
        assert text.index("problem='c'") > text.index("problem='a'")

    def test_result_is_valid_python(self, tmp_path):
        p = self._fake_registry(tmp_path)
        append_to_registry(["    NewProblem(problem='c', solution='d'),"], path=str(p))
        compile(p.read_text(), str(p), "exec")  # raises SyntaxError if malformed
