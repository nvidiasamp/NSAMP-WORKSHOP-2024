from openai import OpenAI


def generate_answer(question: str, context: str) -> str:
    """APIを使ってLLMによる解答を得る関数

    Question (str): 質問内容
        context (str): 解答の根拠になるテキスト情報

    Returns:
        response.choices[0].message.content(str): contextを元に回答したLLMの回答内容

    """
    response = OpenAI().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "あなたは優秀なアシスタントです。これから渡すコンテキストを元に問題に答えてください。答えられる文字数は少ないので単語のみなど簡潔な回答を心がけてください。",
            },
            {
                "role": "user",
                "content": f"Context: {context}. Answer the question: {question}",
            },
        ],
        max_tokens=15,
        temperature=0,
    )
    return str(response.choices[0].message.content)
