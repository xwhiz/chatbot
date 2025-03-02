import uuid

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_qdrant import QdrantVectorStore
from langgraph.graph import START, MessagesState, StateGraph, END
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.tools import tool
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver


vectordb_path = "vector_doc_db"
collection_name = "chat_collection"

print("Creating Qdrant client")
client = QdrantClient(path=vectordb_path)

if client.collection_exists(collection_name):
    print(f"Collection {collection_name} already exists. Using the existing one.")
else:
    print(f"Creating collection: {collection_name}")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE, on_disk=True),
    )
print("Qdrant client created")

print("Creating embeddings")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
print("Embeddings created")

print("Creating vector store")
vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=embeddings,
)


builder = StateGraph(state_schema=MessagesState)
llm = ChatOllama(model="llama3.1")


@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs


# Step 1: Generate an AIMessage that may include a tool-call to be sent.
def query_or_respond(state: MessagesState):
    """Generate tool call for retrieval or respond."""
    llm_with_tools = llm.bind_tools([retrieve])
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# Step 2: Execute the retrieval.
tools = ToolNode([retrieve])


# Step 3: Generate a response using the retrieved content.
def generate(state: MessagesState):
    """Generate answer."""
    # Get generated ToolMessages
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # Format into prompt
    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_message_content = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        f"{docs_content}"
    )
    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_message_content)] + conversation_messages

    response = llm.invoke(prompt)
    return {"messages": [response]}


builder.add_node(query_or_respond)
builder.add_node(tools)
builder.add_node(generate)

builder.set_entry_point("query_or_respond")
builder.add_conditional_edges(
    "query_or_respond",
    tools_condition,
    {END: END, "tools": "tools"},
)
builder.add_edge("tools", "generate")
builder.add_edge("generate", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

session_id = uuid.uuid4()
config = {"configurable": {"thread_id": session_id}}

while True:
    input_message = HumanMessage(content=input("Your message: "))
    # print()
    # print("=" * 20)
    # print()
    for step, metadata in graph.stream(
        {"messages": [input_message]}, config, stream_mode="messages"
    ):
        print(step, end="")
        exit()
        # message = step["messages"][-1]
        # if message.type == "human" or message.type == "ai" and not message.tool_calls:
        #     message.pretty_print()
        # print(step.content, end="")

    # print("\n")
    # print("=" * 20)
    # print()


# chats_by_session_id = {}


# def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
#     chat_history = chats_by_session_id.get(session_id)
#     if chat_history is None:
#         chat_history = InMemoryChatMessageHistory(
#             messages=[
#                 SystemMessage(
#                     content="""Your role: You must answer in 1 paragraph. if it is extremely important only then can you use 2 paragraphs.

#                             NOTE: You must not forget that todays date is
#                             You are an assistant designed for question-answering tasks.
#                             - Use the provided pieces of retrieved context to answer questions as accurately as possible.
#                             - When the context does not directly provide an answer, or when the question is unrelated to the context,
#                             - use your general knowledge to respond appropriately.
#                             - Avoid referencing the retrieved context when it is irrelevant to the question.
#                             """
#                 )
#             ]
#         )
#         chats_by_session_id[session_id] = chat_history
#     return chat_history


# Define the function that calls the model
# def call_model(state: MessagesState, config: RunnableConfig) -> list[BaseMessage]:
#     # Make sure that config is populated with the session id
#     if "configurable" not in config or "session_id" not in config["configurable"]:
#         raise ValueError(
#             "Make sure that the config includes the following information: {'configurable': {'session_id': 'some_value'}}"
#         )
#     # Fetch the history of messages and append to it any new messages.
#     chat_history = get_chat_history(config["configurable"]["session_id"])
#     messages = list(chat_history.messages) + state["messages"]
#     ai_message = llm.invoke(messages)
#     chat_history.add_messages(state["messages"] + [ai_message])
#     return {"messages": ai_message}


# # Define the two nodes we will cycle between
# builder.add_edge(START, "model")
# builder.add_node("model", call_model)

# graph = builder.compile()

# # Here, we'll create a unique session ID to identify the conversation
# session_id = uuid.uuid4()
# config = {"configurable": {"session_id": session_id}}


# while True:
#     input_message = HumanMessage(content=input("Your message: "))
#     print()
#     print("=" * 20)
#     print()
#     for event, metadata in graph.stream(
#         {"messages": [input_message]}, config, stream_mode="messages"
#     ):
#         print(event.content, end="")
#         # event["messages"][-1].pretty_print()

#     print("\n")
#     print("=" * 20)
#     print()
