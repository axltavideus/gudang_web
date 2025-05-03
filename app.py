import logging
from flask import Flask, request, send_file, render_template, jsonify, abort
import pandas as pd
import os
from sqlalchemy import create_engine, inspect

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
PROCESSED_FOLDER = os.getenv("PROCESSED_FOLDER", "processed")
DATABASE_FILE = os.getenv("DATABASE_FILE", "excel_data.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create SQLite engine
engine = create_engine(f"sqlite:///{DATABASE_FILE}", echo=False)

def process_excel_file(filepath):
    """
    Process the uploaded Excel file and return the processed DataFrame.
    """
    xls = pd.ExcelFile(filepath)
    df_raw = pd.read_excel(xls, sheet_name="BOM PENGAJUAN", header=None)

    kode_produk = df_raw.iloc[0, 4]

    # Extract relevant data starting from row 5 (index 4)
    df_data = df_raw.loc[4:, [1, 2, 3, 4, 5, 8]]  # B, C, D, E, F, I
    df_data.columns = ["id_barang", "nama_barang", "qty_per_unit", "total_quantity", "satuan", "keterangan"]
    df_data = df_data.dropna(subset=["id_barang", "nama_barang"], how="all").reset_index(drop=True)

    # Classify rows and assign material group
    jenis_material = []
    material_group = []
    current_group = None

    for val in df_data["id_barang"]:
        try:
            float(val)
            jenis_material.append("Item")
            material_group.append(current_group)
        except (ValueError, TypeError):
            jenis_material.append("Header")
            current_group = str(val).strip()
            material_group.append(None)

    df_data["jenis_material"] = jenis_material
    df_data["material_group"] = material_group

    # Keep only rows where jenis_material is Item
    df_items = df_data[df_data["jenis_material"] == "Item"].copy()

    # Clean up id_barang: remove decimals and convert to string
    df_items["id_barang"] = df_items["id_barang"].apply(lambda x: str(int(float(x))) if pd.notnull(x) else "")

    # Add kode_produk and Checklist columns
    df_items["kode_produk"] = kode_produk
    df_items["Checklist"] = ""

    return df_items, kode_produk

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        logger.warning("No file part in the request")
        return abort(400, description="No file uploaded")

    file = request.files["file"]
    if file.filename == "":
        logger.warning("No selected file")
        return abort(400, description="No selected file")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    logger.info(f"File saved to {filepath}")

    try:
        df_items, kode_produk = process_excel_file(filepath)

        # Save processed Excel
        output_filename = file.filename.replace(".xlsx", "_updated.xlsx")
        output_filepath = os.path.join(PROCESSED_FOLDER, output_filename)
        df_items.to_excel(output_filepath, index=False)
        logger.info(f"Processed file saved to {output_filepath}")

        # Save to DB
        table_name = os.path.splitext(file.filename)[0].replace(" ", "_").replace("-", "_").lower()
        df_items.to_sql(table_name, con=engine, if_exists="replace", index=False)
        logger.info(f"Data saved to database table {table_name}")

        return send_file(output_filepath, as_attachment=True)

    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        return abort(500, description=f"Error processing file: {e}")

# Route to view saved data by table name
@app.route("/view-data/<table_name>")
def view_data(table_name):
    try:
        df = pd.read_sql_table(table_name, con=engine)
        return df.to_html(index=False)
    except Exception as e:
        logger.error(f"Error retrieving data: {e}", exc_info=True)
        return abort(500, description=f"Error retrieving data: {e}")

@app.route("/list-tables")
def list_tables():
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return jsonify(tables)
    except Exception as e:
        logger.error(f"Error listing tables: {e}", exc_info=True)
        return abort(500, description=f"Error listing tables: {e}")

if __name__ == "__main__":
    app.run(debug=True)
