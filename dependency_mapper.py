# dependency_mapper.py
import os
import ast
import graphviz
from pathlib import Path

def find_project_modules(directory):
    """
    Scansiona la directory del progetto per trovare tutti i moduli Python.
    Restituisce un dizionario che mappa i nomi dei moduli ai percorsi dei file.
    """
    project_modules = {}
    root_path = Path(directory).resolve()
    # Nomi delle cartelle da escludere (match esatto, case-sensitive).
    # Verranno ignorati tutti i file e le sottocartelle al loro interno.
    # Nota: __pycache__ è lo standard Python per le cache dei bytecode.
    excluded_dirs = {'src', 'venv', '.git', '__pycache__'}

    for path in root_path.rglob('*.py'):
        # Escludi i file che contengono 'backup' nel nome, in modo case-insensitive
        if 'backup' in path.name.lower():
            print(f"  -> File di backup escluso: {path.name}")
            continue

        # Controlla se una delle cartelle nel percorso è nell'elenco di esclusione
        relative_path = path.relative_to(root_path)
        dir_parts = set(relative_path.parts[:-1])  # Ottieni solo le parti del percorso che sono directory

        if not excluded_dirs.isdisjoint(dir_parts):
            print(f"  -> File in cartella esclusa ({relative_path}): {path.name}")
            continue

        # Calcola il nome del modulo relativo alla root del progetto
        module_name = '.'.join(relative_path.with_suffix('').parts)
        project_modules[module_name] = path
    return project_modules

def get_imports(filepath, project_modules_names):
    """
    Analizza un file Python per estrarre gli import locali al progetto.
    Utilizza l'Abstract Syntax Tree (AST) per un'analisi accurata.
    """
    local_imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in project_modules_names:
                        local_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                # Gestisce import relativi (es. from . import my_module)
                # e assoluti (es. from my_package import my_module)
                if node.module and node.module in project_modules_names:
                    local_imports.add(node.module)

    except (UnicodeDecodeError, SyntaxError, FileNotFoundError) as e:
        print(f"Attenzione: Impossibile analizzare il file {filepath}. Errore: {e}")
    
    return local_imports

def get_node_color(incoming_dependencies_count):
    """
    Restituisce un colore in base al numero di dipendenze in entrata.
    Più dipendenze ha un modulo, più il colore sarà "caldo".
    """
    if incoming_dependencies_count > 5:
        return 'orangered'  # Modulo critico, molto utilizzato
    elif incoming_dependencies_count > 2:
        return 'gold'       # Modulo importante
    elif incoming_dependencies_count > 0:
        return 'lightskyblue' # Modulo standard
    else:
        return 'palegreen'  # Probabile punto di ingresso (es. main.py)

def generate_dependency_graph(directory='.', output_filename='project_dependency_map'):
    """
    Genera un grafo delle dipendenze per tutti i file .py nella directory specificata.
    """
    print("Avvio della scansione dei moduli del progetto...")
    project_modules = find_project_modules(directory)
    project_modules_names = set(project_modules.keys())
    
    if not project_modules:
        print("Nessun file Python (.py) trovato nella directory.")
        return

    print(f"Trovati {len(project_modules)} moduli nel progetto.")
    
    dependencies = {}
    
    print("Analisi delle dipendenze in corso...")
    for module_name, filepath in project_modules.items():
        # Escludiamo lo script stesso dall'analisi
        if module_name == 'dependency_mapper':
            continue
        dependencies[module_name] = get_imports(filepath, project_modules_names)

    # Calcola le dipendenze in entrata per ogni modulo
    print("Calcolo delle dipendenze in entrata per la colorazione...")
    incoming_counts = {name: 0 for name in dependencies}
    for imported_modules in dependencies.values():
        for imported in imported_modules:
            if imported in incoming_counts:
                incoming_counts[imported] += 1

    # Creazione del grafo con Graphviz
    legend = (
        'Mappa delle Dipendenze del Progetto\\n\\n'
        'Legenda Colori (basata su quante volte un modulo viene importato):\\n'
        'Verde: 0 (Punto di ingresso)     '
        'Blu: 1-2 (Standard)     '
        'Giallo: 3-5 (Importante)     '
        'Rosso: >5 (Critico)'
    )
    dot = graphviz.Digraph(
        'ProjectDependencies',
        comment='Mappa delle Dipendenze del Progetto',
        graph_attr={'rankdir': 'LR', 'splines': 'ortho', 'nodesep': '0.8', 'label': legend, 'fontsize': '12'},
        node_attr={'shape': 'box', 'style': 'rounded,filled'},
        edge_attr={'color': 'gray40'}
    )

    print("Generazione del diagramma...")
    for module_name in dependencies.keys():
        count = incoming_counts.get(module_name, 0)
        color = get_node_color(count)
        dot.node(module_name, module_name.replace('_', '\\n'), fillcolor=color)

    for module_name, imported_modules in dependencies.items():
        for imported in imported_modules:
            if imported in dependencies: # Assicurati che il modulo importato sia parte del progetto
                dot.edge(module_name, imported)

    # Salvataggio del grafo
    try:
        dot.render(output_filename, format='png', view=True, cleanup=True)
        print(f"\nSuccesso! La mappa delle dipendenze è stata salvata come '{output_filename}.png'")
        print("Il file è stato aperto automaticamente.")
    except graphviz.backend.ExecutableNotFound:
        print("\n--- ERRORE ---")
        print("Graphviz non trovato. Assicurati di averlo installato e che sia nel PATH di sistema.")
        print("Per istruzioni, visita: https://graphviz.org/download/")
        print(f"Il file sorgente del grafo è stato comunque salvato come '{output_filename}'.")

if __name__ == '__main__':
    project_directory = os.path.dirname(os.path.abspath(__file__))
    generate_dependency_graph(directory=project_directory)
