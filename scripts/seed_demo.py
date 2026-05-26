"""Pre-populate demo telemetry (run once)."""

from maintenance.seed import seed_if_empty

if __name__ == "__main__":
    n = seed_if_empty()
    print(f"Seeded {n} records." if n > 0 else "Already seeded or model missing.")
