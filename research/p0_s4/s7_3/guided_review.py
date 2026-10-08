import csv
from pathlib import Path

folder = Path("research/p0_s4/s7_3/results")
files = sorted(folder.glob("*.review.csv"))

if not files:
    raise SystemExit("No S7.3 review CSV found.")

path = files[0]

with path.open("r", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields or "review_status" not in fields:
    raise SystemExit("Missing review_status column.")

print("\nNBA_MIKE — GUIDED INJURY REVIEW")
print("Source:", path.name)
print("Choices: C = Confirmed, R = Rejected, A = Ambiguous, S = Skip, Q = Quit")
print("Only mark C when you can verify the complete player entry in the PDF.\n")

reviewed_now = 0

for index, row in enumerate(rows):
    if reviewed_now >= 10:
        break

    if row.get("review_status", "").strip().upper() not in ("", "UNREVIEWED"):
        continue

    print("=" * 65)
    print(f"Candidate {index + 1} of {len(rows)}")

    for key, value in row.items():
        if key != "review_status" and value and value.strip():
            print(f"{key}: {value}")

    choice = input("\n[C/R/A/S/Q]: ").strip().upper()

    if choice == "Q":
        break
    if choice == "S":
        continue

    statuses = {"C": "CONFIRMED", "R": "REJECTED", "A": "AMBIGUOUS"}

    if choice not in statuses:
        print("Invalid choice. Skipping.")
        continue

    if choice == "C":
        print("A confirmed row needs its required fields completed.")
        for field in ("game_date", "team", "player", "reason"):
            if field in row and not row.get(field, "").strip():
                row[field] = input(f"{field}: ").strip()

    row["review_status"] = statuses[choice]
    reviewed_now += 1

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved: {row['review_status']}")

print(f"\nSession finished. Newly reviewed: {reviewed_now}")
print("Worksheet:", path)
