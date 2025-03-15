from langchain_ollama import ChatOllama
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from datetime import datetime


def rephrase_question(history: list[str], current_question: str) -> str:
    prompt = """
    <role>Rewrite Agent</role>

    <current-date>%s</current-date>

    <chat-history>
    %s
    </chat-history>

    <instructions>
    Rewrite the given text to enhance clarity, conciseness, and specificity while ensuring the model provides the best possible response.

    - Maintain the original intent.
    - Eliminate ambiguity or vagueness.
    - Use precise language for better understanding.
    - Optimize details based on chat history **only if** they are relevant.
    - If the text is unrelated to chat history, rephrase it independently while preserving its meaning.
    - Avoid redundant or ineffective rephrasings based on past responses.
    - **Respond ONLY with the rewritten text.** No explanations or extra details.
    - Ensure the rewritten text is **concise yet retains all information** from the original.
    - Do not alter the intent of statements, as they may not always be questions.

    <requirement>
    - The rewritten text must be **clear, well-structured, and easy to understand** to guide the model toward an accurate and informative response.
    - If the text is unrelated to previous chats, maintain its meaning without unnecessary contextual adjustments.
    - Avoid rephrasings that could introduce redundancy or ambiguity.
    </requirement>

    <text>{input}</text>
    """ % (
        str(datetime.now().strftime("%Y-%m-%d %A")),
        "\n".join(history).replace("{", "{{").replace("}", "}}"),
    )

    model = ChatOllama(model="qwen2.5:14b", num_ctx=8192)
    qa_chain = (
        {
            "prompt": RunnablePassthrough(),
            "input": RunnablePassthrough(),
        }
        | ChatPromptTemplate.from_template(prompt)
        | model
        | StrOutputParser()
    )

    return qa_chain.invoke(current_question)
