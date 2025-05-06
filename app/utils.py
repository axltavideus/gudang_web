import pandas as pd

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
