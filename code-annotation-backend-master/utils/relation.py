def relations_to_arch_line_relations(relations: list):
    arch_lines_relations = {}
    for line_arch_relation in relations:
        arch_names = line_arch_relation["arch_names"]
        start, end = line_arch_relation["start"], line_arch_relation["end"]
        for arch_name in arch_names:
            if arch_name not in arch_lines_relations:
                arch_lines_relations[arch_name] = []
            arch_lines_relations[arch_name] += list(range(start, end + 1))
    return arch_lines_relations
