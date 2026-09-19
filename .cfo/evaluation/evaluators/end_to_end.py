from evaluation.lineage import evaluate_lineage, lineage_function_result


def run_end_to_end(raw_outputs: dict):
    stories = evaluate_lineage(raw_outputs)
    return lineage_function_result(stories), stories
