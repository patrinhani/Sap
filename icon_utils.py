import os
import struct


def _png_size(png_bytes):
    if png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Arquivo de origem nao e PNG.")
    return struct.unpack(">II", png_bytes[16:24])


def png_to_ico(source_png, target_ico):
    with open(source_png, "rb") as file:
        png_bytes = file.read()

    width, height = _png_size(png_bytes)
    os.makedirs(os.path.dirname(target_ico), exist_ok=True)

    header = struct.pack(
        "<HHHBBBBHHII",
        0,
        1,
        1,
        0 if width >= 256 else width,
        0 if height >= 256 else height,
        0,
        0,
        1,
        32,
        len(png_bytes),
        22,
    )

    with open(target_ico, "wb") as file:
        file.write(header)
        file.write(png_bytes)

    return target_ico


def ensure_app_icon(app_base_path):
    target_ico = os.path.join(app_base_path, "assets", "gcb_icone.ico")
    if os.path.exists(target_ico):
        return target_ico

    source_candidates = [
        os.path.join(app_base_path, "assets", "gcb_icone.png"),
        os.path.join(os.path.dirname(app_base_path), "Sap4Hana", "assets", "gcb_icone.png"),
        r"C:\Users\2160048370\Downloads\Automações\Sap4Hana\assets\gcb_icone.png",
    ]

    for source_png in source_candidates:
        if os.path.exists(source_png):
            return png_to_ico(source_png, target_ico)

    return ""


if __name__ == "__main__":
    print(ensure_app_icon(os.path.dirname(os.path.abspath(__file__))))
