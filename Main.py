"""
Main Orchestrator for System

Flow:
1. Run ingestion pipeline
2. Run scoring pipeline
3. Launch Streamlit UI (UI.py)

Design:
- No business logic here
- Pure execution orchestrator
- Single command entry point
"""

import subprocess
import sys
import os


# -----------------------------
# RUN INGESTION
# -----------------------------

def run_ingestion():
    print("\n[1/3] Running ingestion pipeline...\n")

    result = subprocess.run(
        [sys.executable, "ingestion.py"],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print("Ingestion failed ❌")
        print(result.stderr)
        sys.exit(1)


# -----------------------------
# RUN SCORING
# -----------------------------

def run_scoring():
    print("\n[2/3] Running scoring pipeline...\n")

    result = subprocess.run(
        [sys.executable, "scoring.py"],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print("Scoring failed ❌")
        print(result.stderr)
        sys.exit(1)


# -----------------------------
# RUN STREAMLIT UI
# -----------------------------

def run_streamlit():
    print("\n[3/3] Launching Streamlit UI...\n")

    subprocess.run(
        ["streamlit", "run", "UI.py"],
        check=True
    )


# -----------------------------
# MAIN
# -----------------------------

def main():
    print("\n===================================")
    print(" PIPELINE EXECUTION")
    print("===================================\n")

    run_ingestion()
    run_scoring()

    if os.path.exists("candidates.csv"):
        print("\nPipeline complete ✔ candidates.csv processed\n")
    else:
        print("\nWarning: candidates.csv not found ⚠️\n")

    run_streamlit()


if __name__ == "__main__":
    main()