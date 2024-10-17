from ragas import evaluate

from py.evaluate import ragas_evaluate
from py.load_and_preprocessing import load_and_preprocessing_data

if __name__ == "__main__":
    dataset = load_and_preprocessing_data()
    ragas_input_ds = ragas_evaluate(dataset)
    results = evaluate(ragas_input_ds)

    print(results.to_pandas())
