from pptx import Presentation

path = r"C:\Users\hqy50\Downloads\Group27 Interim Presentation_v3 (1).pptx"
prs = Presentation(path)
print("slide size:", prs.slide_width, prs.slide_height, "slides:", len(prs.slides))
for i, slide in enumerate(prs.slides, 1):
    print(f"\n=== slide {i} ===")
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                text = "".join(run.text for run in para.runs).strip()
                if text:
                    print(f"  T: {text}")
        elif shape.has_table:
            for row in shape.table.rows:
                print("  | " + " | ".join(cell.text.replace("\n", " ") for cell in row.cells))
        elif shape.shape_type == 13:
            print(f"  [picture] {shape.name} {shape.width}x{shape.height}")
    if slide.has_notes_slide:
        notes = slide.notes_slide.notes_text_frame.text.strip()
        if notes:
            print("  NOTES:", notes[:800])
