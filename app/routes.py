import os
import logging
from flask import request, send_file, render_template, jsonify, abort
import pandas as pd
from app import app, UPLOAD_FOLDER, PROCESSED_FOLDER
from app.db import engine, get_inspector
from app.utils import process_excel_file
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

@app.route("/")
def index():
    try:
        inspector = get_inspector()
        tables = inspector.get_table_names()
        return render_template("index.html", tables=tables)
    except Exception as e:
        logger.error(f"Error retrieving tables for index: {e}", exc_info=True)
        return render_template("index.html", tables=[])

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
        base_table_name = os.path.splitext(file.filename)[0]
        table_name = base_table_name[:4].lower()

        # Add the full file name as a column in the DataFrame
        df_items["original_file_name"] = file.filename

        try:
            df_items.to_sql(table_name, con=engine, if_exists="replace", index=False)
            logger.info(f"Data saved to database table {table_name}")
        except OperationalError as op_err:
            logger.error(f"Database connection error: {op_err}", exc_info=True)
            return abort(500, description=f"Database connection error: {op_err}")

        return send_file(output_filepath, as_attachment=True)

    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        return abort(500, description=f"Error processing file: {e}")

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
        inspector = get_inspector()
        tables = inspector.get_table_names()
        return jsonify(tables)
    except Exception as e:
        logger.error(f"Error listing tables: {e}", exc_info=True)
        return abort(500, description=f"Error listing tables: {e}")

@app.route("/tables")
def tables():
    try:
        # Render blank master data page for now
        return render_template("tables.html")
    except Exception as e:
        logger.error(f"Error retrieving tables: {e}", exc_info=True)
