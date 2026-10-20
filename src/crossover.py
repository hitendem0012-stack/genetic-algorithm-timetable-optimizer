
import random


def single_point_crossover(parent1, parent2):
    if len(parent1) != len(parent2):
        raise ValueError("Parents must have the same length.")

    if not parent1:
        return [], []

    # Prefer unique occurrence IDs when sessions have been expanded.
    ids1 = [
        gene.get("gene_id", gene["session_id"])
        for gene in parent1
    ]
    ids2 = [
        gene.get("gene_id", gene["session_id"])
        for gene in parent2
    ]

    if ids1 != ids2:
        raise ValueError(
            "Parents must contain the same gene IDs in order."
        )

    if len(parent1) == 1:
        return [dict(parent1[0])], [dict(parent2[0])]

    point = random.randint(1, len(parent1) - 1)

    child1 = (
        [dict(gene) for gene in parent1[:point]]
        + [dict(gene) for gene in parent2[point:]]
    )

    child2 = (
        [dict(gene) for gene in parent2[:point]]
        + [dict(gene) for gene in parent1[point:]]
    )

    return child1, child2


def crossover(parent1, parent2, probability=0.8):
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1.")

    if random.random() < probability:
        return single_point_crossover(parent1, parent2)

    return (
        [dict(gene) for gene in parent1],
        [dict(gene) for gene in parent2],
    )
