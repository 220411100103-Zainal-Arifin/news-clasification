import re
import sys
from pathlib import Path

from PyPDF2 import PdfReader


def clean_text(text):
    # Menghapus teks header dan disclaimer yang berulang dari dokumen
    text = text.replace(
        "Mahkamah Agung Republik Indonesia\nMahkamah Agung Republik Indonesia\nMahkamah Agung Republik Indonesia\nMahkamah Agung Republik Indonesia\nMahkamah Agung Republik Indonesia\nDirektori Putusan Mahkamah Agung Republik Indonesia\nputusan.mahkamahagung.go.id\n",
        "",
    )
    text = text.replace(
        "\nDisclaimer\nKepaniteraan Mahkamah Agung Republik Indonesia berusaha untuk selalu mencantumkan informasi paling kini dan akurat sebagai bentuk komitmen Mahkamah Agung untuk pelayanan publik, transparansi dan akuntabilitas\npelaksanaan fungsi peradilan. Namun dalam hal-hal tertentu masih dimungkinkan terjadi permasalahan teknis terkait dengan akurasi dan keterkinian informasi yang kami sajikan, hal mana akan terus kami perbaiki dari waktu kewaktu.\nDalam hal Anda menemukan inakurasi informasi yang termuat pada situs ini atau informasi yang seharusnya ada, namun belum tersedia, maka harap segera hubungi Kepaniteraan Mahkamah Agung RI melalui :\nEmail : kepaniteraan@mahkamahagung.go.id",
        "",
    )
    text = text.replace("Telp : 021-384 3348 (ext.318)", "")
    # Menghapus nomor halaman dan elemen unik
    text = re.sub(r'\nHalaman \d+ dari \d+ .*', '', text)
    text = re.sub(r'Halaman \d+ dari \d+ .*', '', text)
    text = re.sub(r'\nHal. \d+ dari \d+ .*', '', text)
    text = re.sub(r'Hal. \d+ dari \d+ .*', '', text)
    text = re.sub(r' +|[\uf0fc\uf0a7\uf0a8\uf0b7]', ' ', text)  # Menghapus bullet points dan spasi berlebih
    text = re.sub(r'[\u2026]+|\.{3,}', '', text)  # Menghapus elipsis atau titik berulang
    return text.strip()  # Menghapus spasi di awal dan akhir


def extract_pdf_to_txt(pdf_path: Path, out_path: Path = None, encoding: str = "utf-8") -> Path:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    texts = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        texts.append(page_text)

    raw = "\n\n".join(texts)
    cleaned = clean_text(raw)

    if out_path is None:
        out_path = pdf_path.with_suffix('.txt')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(cleaned, encoding=encoding)
    return out_path


def main(argv):
    if len(argv) < 2:
        print("Usage: python pdf_to_txt.py <input.pdf> [output.txt]")
        return 2

    pdf = Path(argv[1])
    out = Path(argv[2]) if len(argv) >= 3 else None

    try:
        result = extract_pdf_to_txt(pdf, out)
        print(f"Wrote: {result}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
