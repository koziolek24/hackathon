import os

def save_files_content_to_txt(root_folder, output_file):
    """Rekurencyjnie odczytuje pliki .c, .h i MAKEFILE w folderach
    i zapisuje ich treść do pliku tekstowego."""
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, _, files in os.walk(root_folder):
            for file in files:
                # Sprawdź rozszerzenia plików i nazwę MAKEFILE
                if file.endswith(('.py')) or file.upper() == 'MAKEFILE':
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(f"==== {file_path} ====\n")
                            outfile.write(infile.read())
                            outfile.write("\n\n")
                    except Exception as e:
                        print(f"Nie udało się odczytać pliku {file_path}: {e}")

if __name__ == "__main__":
    # Zmień 'input_folder' na folder, który chcesz przeszukać
    input_folder = "./"
    output_file = "output.txt"
    save_files_content_to_txt(input_folder, output_file)
    print(f"Zawartość plików została zapisana do {output_file}")