from langchain_ollama import ChatOllama
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from datetime import datetime

def current_date() -> str:
    return datetime.now().strftime("%Y-%m-%d %A")



def initialize_qa_chain(llm: ChatOllama, retriever, user_custom_prompt: str, context: str):
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    RAG_TEMPLATE = """
    Your role: ###%s###

    NOTE: You must not forget that todays date is ### %s ###

    You are an assistant designed for question-answering tasks. 
    - Use the provided pieces of retrieved context to answer questions as accurately as possible. 
    - When the context does not directly provide an answer, or when the question is unrelated to the context, 
    - use your general knowledge to respond appropriately. 
    - Avoid referencing the retrieved context when it is irrelevant to the question.
    
    <context>
    ###Previous Chat Context: %s###
    {context}
    </context>

    Answer the following question:
    {question}
    """ % (user_custom_prompt, current_date(), context)

    print("\r\nDEBUG:", RAG_TEMPLATE, "\r\n")


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
