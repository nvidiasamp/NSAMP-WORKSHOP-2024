from datasets import Dataset


def ragas_evaluate(input_data: list) -> Dataset:
    """ragasによる評価を行う関数

        input_data (list):

    Returns:
        Dataset: ragasに入力するためのデータセット

    """
    question_list = [item["question"] for item in input_data]
    context_list = [[item["context"]] for item in input_data]
    answer_list = [item["rag_answer_text"] for item in input_data]
    ground_truth_list = [item["answer_text"] for item in input_data]

    # Create a HuggingFace Dataset
    return Dataset.from_dict(
        {
            "question": question_list,
            "contexts": context_list,
            "answer": answer_list,
            "ground_truth": ground_truth_list,
        },
    )
