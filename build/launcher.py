"""PyInstaller entry for the PaperLife Windows app (products/paperlife/dist/paperlife.exe).

Double-clicking the exe (or running it with no arguments) starts the
interactive ICE-binder flow: the app asks the 12 short questions, then writes
`ice_binder_letter.pdf` into the folder next to the app.

All CLI flags pass through unchanged for power users, e.g.:

    paperlife.exe --product cash --income 2000 --weight "Groceries=50" --weight "Savings=50" --out out
    paperlife.exe --product networth --name "Alex" --assets 1234.56 --liabilities 567.89 --as-of 2026-08-16
    paperlife.exe --product ice --name "Alex" --blood-type "O+"
"""
import sys

from paperlife.cli import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # One-click mode: ask the 12 ICE questions, write the PDF next to the app.
        sys.argv += ["--product", "ice", "--interactive", "--out", "."]
    raise SystemExit(main())
