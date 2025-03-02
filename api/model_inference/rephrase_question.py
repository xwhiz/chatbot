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
    Rewrite the given question to improve clarity, conciseness, and specificity while ensuring the model can provide the best possible response.
    - Maintain the original intent of the question.
    - Resolve any ambiguity or vagueness.
    - Use precise language to enhance understanding.
    - Optimize for relevant details based on past asked questions **only if** they are related.
    - If the question is unrelated to past questions, rephrase it independently without altering its original intent.
    - Consider past responses to avoid redundant or ineffective rephrasings.
    - Your response should ONLY be the rewritten question. No additional information is needed.
    - The rewritten question should be concise and to the point. You must not put information from your own.
    - You must not remove information from the question. the rewritten question should be a better form of the original question, not a completely new question.
    - It is not necessary that the user will always be asking question. So please try not to modify the intent of statements.
    </instructions>

    <requirement>
    - The rewritten question should be clear, well-structured, and easy to understand. It should guide the model towards generating an accurate and informative response.
    - If the question is unrelated to previous ones, ensure that its original meaning is preserved without unnecessary contextual adjustments.
    - Avoid rephrasings that could lead to redundant or unclear answers.
    </requirement>

    <question>{input}</question>
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
