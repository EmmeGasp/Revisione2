import os
import ast

def scan_py_files(directory):
    inventory = []
    for root, _, files in os.walk(directory):
        for fname in files:
            # Escludi file che contengono 'backup' (case-insensitive)
            if fname.endswith('.py') and 'backup' not in fname.lower():
                fpath = os.path.join(root, fname)
                with open(fpath, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read(), filename=fname)
                    except Exception as e:
                        print(f"⚠️ Errore parsing {fname}: {e}")
                        continue
                    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                    defs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                    inventory.append({
                        'file': fpath,
                        'classes': classes,
                        'functions': defs
                    })
    return inventory

def print_inventory(inventory, file=None):
    for entry in inventory:
        #line = f"\n📄 File: {os.path.basename(entry['file'])}\n"
        line = f"\n📄 File: {os.path.basename(entry['file'])} ({os.path.dirname(entry['file'])})\n"
        if file:
            file.write(line)
        else:
            print(line, end="")
        if entry['classes']:
            cline = "  Classi:\n" + "".join(f"    - {c}\n" for c in entry['classes'])
            if file:
                file.write(cline)
            else:
                print(cline, end="")
        if entry['functions']:
            fline = "  Funzioni/Metodi:\n" + "".join(f"    - {f}\n" for f in entry['functions'])
            if file:
                file.write(fline)
            else:
                print(fline, end="")

if __name__ == "__main__":
    directory = os.path.dirname(__file__)
    inventory = scan_py_files(directory)
    # Salva su file oltre che stampare a video
    output_path = os.path.join(directory, "inventory_report.txt")
    with open(output_path, "w", encoding="utf-8") as outf:
        print_inventory(inventory, file=outf)
    print_inventory(inventory)
    print(f"\n✅ Inventario salvato in: {output_path}")
