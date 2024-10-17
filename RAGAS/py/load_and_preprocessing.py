from datasets import concatenate_datasets, load_dataset

from py.generate_answer import generate_answer


def load_and_preprocessing_data() -> list[dict[str, str]]:
    """データのダウンロードと前処理

    Returns:
        _type_:list

    """
    jaquad_dataset = load_dataset("SkelterLabsInc/JaQuAD")

    combined_data = concatenate_datasets(
        [jaquad_dataset["train"], jaquad_dataset["validation"]],
    )

    # 前処理：正解データの準備
    combined_data_processed = []
    for item in combined_data:
        answer_text = item["answers"]["text"][0] if item["answers"]["text"] else ""
        answer_start = (
            item["answers"]["answer_start"][0]
            if item["answers"]["answer_start"]
            else -1
        )
        combined_data_processed.append(
            {
                "question": item["question"],
                "context": item["context"],
                "answer_text": answer_text,
                "answer_start": answer_start,
            },
        )

    # データが多いため10件に絞る
    combined_data_processed = combined_data_processed[:10]

    for item in combined_data_processed:
        item["rag_answer_text"] = generate_answer(item["question"], item["context"])

    return combined_data_processed
