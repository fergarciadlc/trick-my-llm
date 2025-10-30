import argparse
from src.core.runner import load_config, run_experiment, save_outputs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Path to experiment YAML")
    args = ap.parse_args()

    cfg = load_config(args.config)
    rows = run_experiment(cfg)
    outdir = save_outputs(rows)
    print(f"Saved outputs to: {outdir}")

if __name__ == "__main__":
    main()
