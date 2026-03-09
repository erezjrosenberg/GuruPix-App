"""
GuruPix training pipeline. Stage 0: smoke mode only.
Full training (rankers, metrics, model registry) in Stage 10.
"""
import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="GuruPix training")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test (tiny dataset)")
    args = parser.parse_args()

    if args.smoke:
        # Stage 0: just ensure script runs; no real training yet
        print("Smoke run: training pipeline placeholder OK")
        return 0

    print("Full training not implemented until Stage 10.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
