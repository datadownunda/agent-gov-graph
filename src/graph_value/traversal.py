"""Generic finite traversal with explicit cycles, origins and incompleteness."""
from src.graph_value.results import result, stable


def walk(graph, start, *, reverse=False, relations=None, depth=None, limit=10000):
    if start not in graph.nodes:
        return result('DEPENDENCIES', complete=False, unresolved=[start])
    todo = [(start,[start],[],[],[])]
    found, paths, cycles, missing = {start}, [], [], set()
    complete = True
    adjacency = graph.incoming if reverse else graph.outgoing
    while todo:
        node, visited, fields, categories, provenance = todo.pop()
        if depth is not None and len(fields) >= depth:
            continue
        for edge in adjacency.get(node, []):
            if relations is not None and edge['relation'] not in relations:
                continue
            other = edge['source'] if reverse else edge['target']
            path = {'records':visited + [other], 'fields':fields + [edge['field']],
                    'categories':categories + [edge['category']],
                    'edge_provenance':provenance + [{'origin':edge['origin'],'pointer':edge['pointer']}],
                    'origins':[graph.nodes[k]['origin'] for k in visited + [other] if k in graph.nodes]}
            if other in visited:
                cycles.append(path)
                continue
            if other not in graph.nodes:
                missing.add(other)
                continue
            found.add(other)
            paths.append(path)
            if len(paths) >= limit:
                complete = False
                todo.clear()
                break
            todo.append((other,path['records'],path['fields'],path['categories'],path['edge_provenance']))
    return result('DEPENDENCIES', found, paths, cycles=sorted(cycles,key=stable),
                  unresolved=sorted(missing),complete=complete and not missing)
