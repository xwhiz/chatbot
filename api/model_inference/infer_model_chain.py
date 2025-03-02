from langchain_ollama import ChatOllama
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from datetime import datetime
import html


def current_date() -> str:
    return datetime.now().strftime("%Y-%m-%d %A")


def initialize_qa_chain(
    llm: ChatOllama,
    retriever,
    user_custom_prompt: str,
    chat_history: str,
    use_retriever: bool = False,
):
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chat_history = chat_history.replace("{", "{{").replace("}", "}}")

    system_prompt = """
    <role>%s</role>

    <current-date>%s</current-date>
    

    <instructions>
    You are an assistant designed for question-answering tasks. 
    - Use the provided pieces of retrieved context to answer questions as accurately as possible. 
    - When the context does not directly provide an answer, or when the question is unrelated to the context, 
    - use your general knowledge to respond appropriately. 
    - Avoid referencing the retrieved context when it is irrelevant to the question.
    </instructions>

    <chat-history>%s</chat-history>
    """ % (user_custom_prompt, current_date(), chat_history)

    print("\r\nDEBUG:", system_prompt, "\n\r\n")
    print("Should use retriever:", use_retriever)

    if use_retriever:
        system_prompt += """
        <context>
        {context}
        </context>

        Answer the following question:
        <question>{question}</question>
        """
        rag_prompt = ChatPromptTemplate.from_template(system_prompt)
        qa_chain = (
            {
                "context": retriever | format_docs,
                "customPrompt": RunnablePassthrough(),
                "question": RunnablePassthrough(),
            }
            | rag_prompt
            | llm
            | StrOutputParser()
        )
    else:
        system_prompt += """
        Answer the following question:
        <question>{question}</question>
        """
        rag_prompt = ChatPromptTemplate.from_template(system_prompt)
        qa_chain = (
            {
                "customPrompt": RunnablePassthrough(),
                "question": RunnablePassthrough(),
            }
            | rag_prompt
            | llm
            | StrOutputParser()
        )

    return qa_chain
