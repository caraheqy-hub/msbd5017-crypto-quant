from pathlib import Path

from pptx import Presentation

SRC = Path(r"C:\Users\hqy50\Downloads\Group27 Interim Presentation_v3 (1).pptx")
DST = Path(r"C:\Users\hqy50\Downloads\Group27 Interim Presentation_v6.pptx")
COPY = Path(r"D:\Desktop\hkust_sem1\5017\crypto_project\presentations\interim\group27_interim_v6.pptx")

TEXT_REPLACEMENTS = [
    (
        "Chainlab anchoring and independent verification of the delivered package",
        "Local-chain anchoring and independent verification of the delivered package (Chainlab testnet pending)",
    ),
    ("packages anchored", "packages anchored (local)"),
    ("testnet anchoring and verification completed", "local-chain anchoring and verification; Chainlab testnet pending"),
    (
        "We used a smart contract on Chainlab to store the hashes of all three audit packages, while keeping the actual files off-chain. All original packages passed verification.",
        "We anchored the hashes of all three audit packages on a local Hardhat chain and read them back for verification.",
    ),
    (
        "Chainlab records for the three audit packages",
        "local-chain records for the three audit packages",
    ),
]

EXACT_REPLACEMENTS = {"Chainlab": "Local chain"}

FEEDBACK = "Feedback: When does on-chain version registration add value beyond Git or a database?"


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
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                total += fix_frame(shape.text_frame)
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        total += fix_frame(cell.text_frame)
        if slide.has_notes_slide:
            total += fix_frame(slide.notes_slide.notes_text_frame)

    # Put the feedback question back into the "Main Challenges" block.
    slide4 = prs.slides[3]
    for shape in slide4.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip().startswith("Main Challenges"):
            para = shape.text_frame.add_paragraph()
            run = para.add_run()
            run.text = FEEDBACK
            print("feedback added to:", shape.name)
            break

    prs.save(str(DST))
    COPY.parent.mkdir(parents=True, exist_ok=True)
    COPY.write_bytes(DST.read_bytes())
    print(f"replacements: {total}")
    print(f"saved: {DST}")


if __name__ == "__main__":
    main()
