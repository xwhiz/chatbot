from langchain_ollama import ChatOllama
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain.prompts import ChatPromptTemplate


def initialize_qa_chain(llm: ChatOllama, retriever):
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    RAG_TEMPLATE = """
    You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question as accurately as possible. If the context does not directly provide an answer, or if the question is unrelated to the context, use your general knowledge to respond appropriately and forget about the context.

    <context>
    {context}
    </context>

    Answer the following question:
    {question}
    """

    rag_prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt
        | llm
        | StrOutputParser()
    )

    return qa_chain
