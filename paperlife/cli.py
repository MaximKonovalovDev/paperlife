"""PaperLife command-line generator.

Usage:
    python -m engine.paperlife --product ice      --name "Alex" ... [--out DIR] [--paper letter|a4]
    python -m engine.paperlife --product cash     --income 2000 --weight "Groceries=50" --weight "Savings=50"
    python -m engine.paperlife --product networth --name "Alex" --as-of 2026-08-16 --assets 1234.56 --liabilities 567.89
    python -m engine.paperlife --product ice --json fields.json
    python -m engine.paperlife --product ice            # prompts for the 12 fields (TTY)

Exit codes: 0 = success, 1 = runtime error, 2 = invalid input/usage.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from decimal import Decimal, InvalidOperation

from . import PRODUCTS, __version__
from .money import parse_dollars, parse_weight, dollars_to_cents
from .ice import ICE_FIELDS, build_ice_pages
from .cash import build_cash_pages
from .networth import build_cert_page
from .pdfout import write_pdf
from .previews import render_preview

PAPERS = ("letter", "a4")

ICE_FLAGS = [
    ("name", "--name"), ("phone", "--phone"), ("address", "--address"),
    ("emergency_name", "--emergency-name"), ("emergency_phone", "--emergency-phone"),
    ("blood_type", "--blood-type"), ("allergies", "--allergies"),
    ("medications", "--medications"), ("doctor", "--doctor"),
    ("doctor_phone", "--doctor-phone"), ("insurance", "--insurance"),
    ("policy", "--policy"),
]


def _add_ice_args(p: argparse.ArgumentParser):
    for key, flag in ICE_FLAGS:
        prompt = dict(ICE_FIELDS)[key]
        p.add_argument(flag, dest=key, metavar="VALUE",
                       help=f"ICE field: {prompt}")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="paperlife",
        description="PaperLife printable money-life PDF kit generator.",
    )
    p.add_argument("--version", action="version", version=f"paperlife {__version__}")
    p.add_argument("--product", choices=PRODUCTS, required=True,
                   help="which product to generate")
    p.add_argument("--out", default="renders", metavar="DIR",
                   help="output directory (default: renders/)")
    p.add_argument("--paper", choices=PAPERS, default="letter",
                   help="page size (default: letter)")
    p.add_argument("--preview", action="store_true",
                   help="also write PNG previews (the listing images)")
    p.add_argument("--json", metavar="FILE", dest="json_file",
                   help="read field values from a JSON file")
    p.add_argument("--interactive", action="store_true",
                   help="prompt for missing fields even without a TTY")

    sub = p.add_argument_group("cash product")
    sub.add_argument("--income", metavar="DOLLARS", help="monthly income (e.g. 2000 or 500.17)")
    sub.add_argument("--weight", metavar="NAME=PCT", action="append", default=[],
                     help="category weight, repeatable; weights must sum to exactly 100%")
    sub.add_argument("--assets", metavar="DOLLARS", help="networth: total assets")
    sub.add_argument("--liabilities", metavar="DOLLARS", help="networth: total liabilities")
    sub.add_argument("--as-of", metavar="YYYY-MM-DD", help="networth: as-of date")
    _add_ice_args(p)
    return p


def _load_json(args) -> dict:
    if not args.json_file:
        return {}
    with open(args.json_file, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("--json must contain a JSON object of field values")
    return data


def _prompt(text: str) -> str:
    try:
        return input(f"{text}: ").strip()
    except EOFError:
        return ""


def _collect_ice(args, data: dict, interactive: bool) -> dict:
    fields = {key: data.get(key) or getattr(args, key) or "" for key, _ in ICE_FLAGS}
    if "date_prepared" in data:
        fields["date_prepared"] = str(data["date_prepared"])
    if interactive:
        for key, prompt in ICE_FIELDS:
            if not str(fields.get(key) or "").strip():
                fields[key] = _prompt(prompt)
    return fields


def _collect_cash(args, data: dict, interactive: bool) -> tuple[str, dict]:
    income = data.get("income") or args.income
    weights: dict = {}
    if "weights" in data:
        weights.update(data["weights"])
    for w in args.weight:
        if "=" not in w:
            raise ValueError(f"--weight must be NAME=PCT, got {w!r}")
        name, pct = w.split("=", 1)
        name = name.strip()
        if not name:
            raise ValueError(f"--weight category name must not be empty, got {w!r}")
        weights[name] = pct.strip()
    if interactive and not income:
        income = _prompt("Monthly income (e.g. 2000 or 500.17)")
    if interactive and not weights:
        while True:
            name = _prompt("Category name (blank to finish)")
            if not name:
                break
            pct = _prompt(f"Weight for '{name}' in percent")
            weights[name] = pct
    if not income:
        raise ValueError("cash product requires --income (or --json with 'income')")
    if not weights:
        raise ValueError("cash product requires at least one --weight (or --json 'weights')")
    return income, weights


def _collect_networth(args, data: dict, interactive: bool) -> dict:
    fields = {
        "name": data.get("name") or args.name or "",
        "as_of": data.get("as_of") or args.as_of or "",
        "assets": data.get("assets") or args.assets,
        "liabilities": data.get("liabilities") or args.liabilities,
    }
    if interactive:
        if not fields["name"]:
            fields["name"] = _prompt("Full name (blank = unsigned line)")
        if not fields["as_of"]:
            fields["as_of"] = _prompt("As-of date (YYYY-MM-DD)")
        if not fields["assets"]:
            fields["assets"] = _prompt("Total assets")
        if not fields["liabilities"]:
            fields["liabilities"] = _prompt("Total liabilities")
    if not fields["assets"]:
        raise ValueError("networth product requires --assets (or --json 'assets')")
    if not fields["liabilities"]:
        raise ValueError("networth product requires --liabilities (or --json 'liabilities')")
    return fields


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    interactive = args.interactive or sys.stdin.isatty()

    try:
        data = _load_json(args)
        out_dir = pathlib.Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)

        if args.product == "ice":
            fields = _collect_ice(args, data, interactive)
            page_fns = build_ice_pages(fields, paper=args.paper)
            stem = f"ice_binder_{args.paper}"
            title = "PaperLife ICE Binder"
        elif args.product == "cash":
            income, weights = _collect_cash(args, data, interactive)
            parse_dollars(income)  # validate before drawing
            for name, w in weights.items():
                parse_weight(w)
            page_fns = build_cash_pages(income, weights, paper=args.paper)
            stem = f"cash_kit_{args.paper}"
            title = "PaperLife Cash Stuffing Kit"
        else:
            fields = _collect_networth(args, data, interactive)
            page_fns = build_cert_page(fields, paper=args.paper)
            stem = f"networth_{args.paper}"
            title = "PaperLife Certificate of Net Worth"

        pdf_path = out_dir / f"{stem}.pdf"
        pages = write_pdf(page_fns, pdf_path, paper=args.paper, title=title)
        print(f"wrote {pdf_path} ({pages} pages)")

        if args.preview:
            png_dir = out_dir / "png"
            png_dir.mkdir(parents=True, exist_ok=True)
            for i, fn in enumerate(page_fns):
                png = png_dir / f"{stem}_p{i + 1:02d}.png"
                render_preview([fn], png, paper=args.paper, scale=2.0)
                print(f"wrote {png}")
        return 0

    except (ValueError, InvalidOperation, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
