import json
from pathlib import Path
from sqlmodel import SQLModel, Field
import datetime

# --- CONFIG ---
JSON_FILE = "/app/app/sharepoint/DepotMasterMetadata.json"
OUTPUT_FILE = "/app/app/models/models_depot.py"

# Type mapping
TYPE_MAP = {
    "str": "str",
    "float": "float",
    "int": "int",
    "datetime": "datetime",
}

MAX_LENGTH = 255  # For string fields


def generate_models(sheet: dict) -> str:
    """
    Generate SQLModel table + Pydantic schemas for a sheet.
    """
    class_name = sheet["formatted_name"]

    # Base schema
    lines = [f"class {class_name}Base(SQLModel):"]
    for col in sheet["columns"]:
        col_name = col["formatted_name"]
        col_type = TYPE_MAP.get(col["type"], "str")
        if col_type == "str":
            lines.append(f"    {col_name}: str | None = Field(default=None, max_length={MAX_LENGTH})")
        elif col_type == "float":
            lines.append(f"    {col_name}: float | None = Field(default=None)")
        elif col_type == "int":
            lines.append(f"    {col_name}: int | None = Field(default=None)")
        elif col_type == "datetime":
            lines.append(f"    {col_name}: datetime | None = Field(default=None)")
        else:
            lines.append(f"    {col_name}: str | None = Field(default=None)")
    lines.append("")  # empty line

    # Create schema
    lines.append(f"class {class_name}Create({class_name}Base):")
    lines.append("    pass\n")

    # Update schema (all optional)
    lines.append(f"class {class_name}Update({class_name}Base):")
    lines.append("    pass\n")

    # Public schema
    lines.append(f"class {class_name}Public({class_name}Base):")
    lines.append("    instance_id: int\n")

    # List schema
    lines.append(f"class {class_name}List(SQLModel):")
    lines.append(f"    data: list[{class_name}Public]")
    lines.append("    count: int\n")

    # Table class
    lines.append(f"class {class_name}({class_name}Base, table=True):")
    lines.append("    instance_id: int = Field(default_factory=int, primary_key=True)\n")

    # Generic message
    lines.append("class Message(SQLModel):")
    lines.append("    message: str\n")

    return "\n".join(lines)


def main():
    with open(JSON_FILE, "r") as f:
        data = json.load(f)

    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_models = [
        "from sqlmodel import SQLModel, Field",
        "from datetime import datetime\n"
    ]

    for sheet in data.get("sheets", []):
        all_models.append(generate_models(sheet))

    with open(output_path, "w") as f:
        f.write("\n".join(all_models))

    print(f"✅ Models generated successfully at {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
