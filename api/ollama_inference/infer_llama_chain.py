from langchain_ollama import ChatOllama
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain.prompts import ChatPromptTemplate


def initialize_qa_chain(llm: ChatOllama, retriever, custom_prompt: str):
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    RAG_TEMPLATE = """
    Your role: ###custom_prompt###

    You are an assistant designed for question-answering tasks. 
    - Use the provided pieces of retrieved context to answer questions as accurately as possible. 
    - When the context does not directly provide an answer, or when the question is unrelated to the context, 
    - use your general knowledge to respond appropriately. 
    - Avoid referencing the retrieved context when it is irrelevant to the question.
    
    <context>
    {context}
    </context>

    Answer the following question:
    {question}
    """
    RAG_TEMPLATE = RAG_TEMPLATE.replace("custom_prompt", custom_prompt)

    rag_prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)
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

    return qa_chain
