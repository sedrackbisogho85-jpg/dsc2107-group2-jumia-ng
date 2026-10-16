from pathlib import Path

import nbformat
from nbclient import NotebookClient


repository_root = Path(__file__).resolve().parents[1]
notebook_path = repository_root / "notebooks" / "jumia_analysis.ipynb"

notebook = nbformat.read(notebook_path, as_version=4)
client = NotebookClient(
    notebook,
    timeout=180,
    kernel_name="python3",
    resources={"metadata": {"path": str(repository_root)}},
)
client.execute()
nbformat.write(notebook, notebook_path)

code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
errors = [
    output
    for cell in code_cells
    for output in cell.get("outputs", [])
    if output.get("output_type") == "error"
]
png_outputs = [
    output
    for cell in code_cells
    for output in cell.get("outputs", [])
    if "image/png" in output.get("data", {})
]

print(f"Notebook: {notebook_path}")
print(f"Executed code cells: {sum(cell.execution_count is not None for cell in code_cells)}/{len(code_cells)}")
print(f"Error outputs: {len(errors)}")
print(f"PNG chart outputs: {len(png_outputs)}")
