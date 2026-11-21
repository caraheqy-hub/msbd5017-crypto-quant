from pathlib import Path

from pptx import Presentation

SRC = Path(r"C:\Users\hqy50\Downloads\Group27 Interim Presentation_v3 (1).pptx")
DST = Path(r"C:\Users\hqy50\Downloads\Group27 Interim Presentation_v4.pptx")
COPY = Path(r"D:\Desktop\hkust_sem1\5017\crypto_project\presentations\interim\group27_interim_v4.pptx")

# Longest / most specific replacements first, so generic words do not pre-empt them.
TEXT_REPLACEMENTS = [
    (
        "Chainlab anchoring and independent verification of the delivered package",
        "Chainlab anchoring (script ready; testnet step pending) and independent verification of the delivered package",
    ),
    ("packages anchored", "audit packages ready"),
    ("Original: PASS", "Original: PASS (local)"),
    ("Modified copy: FAIL", "Modified copy: FAIL (local)"),
    ("testnet anchoring and verification completed", "local verification; testnet anchoring pending"),
    (
        "We used a smart contract on Chainlab to store the hashes of all three audit packages, while keeping the actual files off-chain. All original packages passed verification.",
        "We computed SHA-256 for all three audit packages and verified them locally; anchoring them on Chainlab is the next step.",
    ),
    (
        "Chainlab records for the three audit packages",
        "local hash records for the three audit packages (on-chain anchoring pending)",
    ),
]

# The chain pill on slide 4 is a single run whose whole text is "Chainlab".
EXACT_REPLACEMENTS = {"Chainlab": "Chainlab (next)"}


def fix_frame(frame):
    changed = 0
    for para in frame.paragraphs:
        for run in para.runs:
            for old, new in TEXT_REPLACEMENTS:
                if old in run.text:
                    run.text = run.text.replace(old, new)
                    changed += 1
            if run.text.strip() in EXACT_REPLACEMENTS:
                run.text = EXACT_REPLACEMENTS[run.text.strip()]
                changed += 1
    return changed


def main():
    prs = Presentation(str(SRC))
    total = 0
    for index, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            if shape.has_text_frame:
                total += fix_frame(shape.text_frame)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        total += fix_frame(cell.text_frame)
        if slide.has_notes_slide:
            total += fix_frame(slide.notes_slide.notes_text_frame)
        print(f"slide {index}: done")

    prs.save(str(DST))
    COPY.parent.mkdir(parents=True, exist_ok=True)
    COPY.write_bytes(DST.read_bytes())
    print(f"replacements applied: {total}")
    print(f"saved: {DST}")


if __name__ == "__main__":
    main()
