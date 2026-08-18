"""CLI golden tests — the documented commands must work exactly as written."""

import json
import pathlib
import subprocess
import sys

from paperlife.cli import main
from paperlife.pdfout import count_pages, count_text
from paperlife.theme import DISCLAIMER_ASCII_PROBE


def test_cli_ice_minimal(tmp_path):
    code = main(["--product", "ice", "--name", "Test Person", "--out", str(tmp_path)])
    assert code == 0
    pdf = tmp_path / "ice_binder_letter.pdf"
    assert pdf.exists()
    assert count_pages(pdf) == 8
    assert count_text(pdf, DISCLAIMER_ASCII_PROBE) >= 8


def test_cli_cash_exact_math_and_preview(tmp_path):
    code = main(["--product", "cash", "--income", "500.17",
                 "--weight", "Groceries=50", "--weight", "Savings=30",
                 "--weight", "Fun=20", "--out", str(tmp_path), "--preview"])
    assert code == 0
    assert (tmp_path / "cash_kit_letter.pdf").exists()
    assert (tmp_path / "png" / "cash_kit_letter_p01.png").exists()


def test_cli_cash_weights_not_100_exits_2(tmp_path, capsys):
    code = main(["--product", "cash", "--income", "2000",
                 "--weight", "A=50", "--out", str(tmp_path)])
    assert code == 2
    assert "must sum to exactly 100%" in capsys.readouterr().err


def test_cli_cash_bad_income_exits_2(tmp_path, capsys):
    code = main(["--product", "cash", "--income", "1.999",
                 "--weight", "A=100", "--out", str(tmp_path)])
    assert code == 2
    assert "2 decimal places" in capsys.readouterr().err


def test_cli_networth_negative_exit_0(tmp_path):
    code = main(["--product", "networth", "--name", "N. Test",
                 "--as-of", "2026-08-16", "--assets", "3500",
                 "--liabilities", "6000", "--out", str(tmp_path)])
    assert code == 0
    pdf = tmp_path / "networth_letter.pdf"
    assert count_pages(pdf) == 1
    data = pdf.read_bytes()
    assert b"Net Worth" in data
    assert b"-" + b"$2,500.00" in data  # honest negative


def test_cli_json_file(tmp_path):
    fields = {"name": "JSON Person", "blood_type": "AB+"}
    jf = tmp_path / "fields.json"
    jf.write_text(json.dumps(fields), encoding="utf-8")
    code = main(["--product", "ice", "--json", str(jf), "--out", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "ice_binder_letter.pdf").exists()


def test_engine_shim_runs_from_repo_root():
    """The documented invocation `python -m engine.paperlife` must work."""
    root = pathlib.Path(__file__).resolve().parent.parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "engine.paperlife", "--product", "networth",
         "--name", "Shim Test", "--assets", "100", "--liabilities", "50",
         "--out", str(root / "renders" / "_cli_check")],
        cwd=root, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    pdf = root / "renders" / "_cli_check" / "networth_letter.pdf"
    assert pdf.exists()
    pdf.unlink()
    (root / "renders" / "_cli_check").rmdir()
