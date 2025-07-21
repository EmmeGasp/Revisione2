import os
import ast

def scan_py_files(directory):
    excluded_files = {'dependency_mapper.py', 'inventory_classes_functions.py', '__init__.py', 'GeneraTabellaRiepilogativaCertificates.py', 'TEMPLATE.py'}
    inventory = []
    for root, _, files in os.walk(directory):
        if 'venv' in root:
            continue
        for fname in files:
            if fname in excluded_files:
                continue
            if fname.endswith('.py') and 'backup' not in fname.lower():
                fpath = os.path.join(root, fname)
                if os.path.basename(fpath) == '__init__.py':
                    continue
                with open(fpath, 'r', encoding='utf-8') as f:
                    try:
                        tree = ast.parse(f.read(), filename=fname)
                    except Exception as e:
                        print(f"⚠️ Errore parsing {fname}: {e}")
                        continue
                    # Annota i parent PRIMA di raccogliere classi/funzioni
                    for node in ast.walk(tree):
                        for child in ast.iter_child_nodes(node):
                            child.parent = node
                    classes = []
                    functions = []
                    func_class_map = {}
                    class_func_map = {}
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            classes.append(node.name)
                            class_func_map[node.name] = []
                        elif isinstance(node, ast.FunctionDef):
                            # Trova la classe di appartenenza (se esiste)
                            parent = node
                            class_name = None
                            while hasattr(parent, 'parent'):
                                parent = parent.parent
                                if isinstance(parent, ast.ClassDef):
                                    class_name = parent.name
                                    break
                            functions.append(node.name)
                            func_class_map[node.name] = class_name if class_name else "Nessuna classe"
                            # Raggruppa per classe
                            if class_name:
                                class_func_map[class_name].append(node.name)
                            else:
                                class_func_map.setdefault("Nessuna classe", []).append(node.name)
                    inventory.append({
                        'file': fpath,
                        'classes': classes,
                        'functions': functions,
                        'func_class_map': func_class_map,
                        'class_func_map': class_func_map,
                        'num_classes': len(classes),
                        'num_functions': len(functions),
                        'size': os.path.getsize(fpath)
                    })
    return inventory

def print_inventory(inventory, file=None):
    for entry in inventory:
        line = (
            f"\n📄 File: {os.path.basename(entry['file'])} ({os.path.dirname(entry['file'])})\n"
            f"    Dimensione: {entry['size']} byte\n"
            f"    Classi trovate: {entry['num_classes']} | Funzioni trovate: {entry['num_functions']}\n"
        )
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
            fline = "  Funzioni/Metodi:\n" + "".join(
                f"    - {f} ({entry['func_class_map'].get(f, 'Nessuna classe')})\n"
                for f in entry['functions']
            )
            if file:
                file.write(fline)
            else:
                print(fline, end="")

def print_inventory_grouped(inventory, file=None):
    for entry in inventory:
        line = (
            f"\n📄 File: {os.path.basename(entry['file'])} ({os.path.dirname(entry['file'])})\n"
            f"    Dimensione: {entry['size']} byte\n"
            f"    Classi trovate: {entry['num_classes']} | Funzioni trovate: {entry['num_functions']}\n"
        )
        if file:
            file.write(line)
        else:
            print(line, end="")
        # Raggruppa per classe
        for cls in entry['class_func_map']:
            cline = f"  Classe: {cls}\n"
            if file:
                file.write(cline)
            else:
                print(cline, end="")
            for func in entry['class_func_map'][cls]:
                fline = f"    - {func}\n"
                if file:
                    file.write(fline)
                else:
                    print(fline, end="")

if __name__ == "__main__":
    directory = os.path.dirname(__file__)
    inventory = scan_py_files(directory)
    # Primo report: funzioni con classe accanto
    output_path = os.path.join(directory, "inventory_report.txt")
    with open(output_path, "w", encoding="utf-8") as outf:
        print_inventory(inventory, file=outf)
    print_inventory(inventory)
    print(f"\n✅ Inventario salvato in: {output_path}")
    # Secondo report: raggruppato per classe
    output_path_grouped = os.path.join(directory, "inventory_report_grouped.txt")
    with open(output_path_grouped, "w", encoding="utf-8") as outf2:
        print_inventory_grouped(inventory, file=outf2)
    print(f"\n✅ Inventario raggruppato salvato in: {output_path_grouped}")
    with open(output_path_grouped, "w", encoding="utf-8") as outf2:
        print_inventory_grouped(inventory, file=outf2)
    print(f"\n✅ Inventario raggruppato salvato in: {output_path_grouped}")
