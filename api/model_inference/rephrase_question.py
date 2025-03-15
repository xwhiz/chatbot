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
    Rewrite the given text to improve clarity, conciseness, and specificity while ensuring the model can provide the best possible response.
    - Maintain the original intent of the text.
    - Resolve any ambiguity or vagueness.
    - Use precise language to enhance understanding.
    - Optimize for relevant details based on chat history **only if** they are related.
    - If the text is unrelated to chat history, rephrase it independently without altering its original intent.
    - Consider past responses to avoid redundant or ineffective rephrasings.
    - Your response should ONLY be the rewritten text. No additional information is needed.
    - The rewritten text should be concise and to the point.
    - You must not remove information from the text. the rewritten text should be a better form of the original text, not a completely new text.
    - It is not necessary that the user will always be asking question. So please try not to modify the intent of statements.
    </instructions>

    <requirement>
    - The rewritten text should be clear, well-structured, and easy to understand. It should guide the model towards generating an accurate and informative response.
    - If the text is unrelated to previous ones, ensure that its original meaning is preserved without unnecessary contextual adjustments.
    - Avoid rephrasings that could lead to redundant or unclear answers.
    </requirement>

    <text>{input}</text>
    """ % (
        str(datetime.now().strftime("%Y-%m-%d %A")),
        "\n".join(history).replace("{", "{{").replace("}", "}}"),
    )

    model = ChatOllama(model="llama3.1", num_ctx=8192)
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
