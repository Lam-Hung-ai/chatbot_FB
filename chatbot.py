from typing import Annotated, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from vector_database.vector_database import VectorDatabase

from utils.read_env import GoogleKey
from prompt_guide.prompt import prompt

key = GoogleKey(pattern="GOOGLE_API_KEY", num_keys=2)
class State(TypedDict):
    messages: Annotated[list, add_messages]
    age_group_children: str
    decision: str
    query: str
    info: list
    parent_name: str
    vector_db: VectorDatabase 
    
graph_builder = StateGraph(State)

async def llm_router(state: State):
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=key.get_key())
    messages = [SystemMessage(prompt['llm_router'])] + state["messages"]
    result = await llm.ainvoke(messages)

    result = "retrieval" if result.content == "retrieval" else "normal"
    return {"decision": result}

async def llm_decision(state: State):
    return (
        "normal"
        if state['decision'] == "normal"
        else "retrieval"
    )

async def normal_answer(state: State):
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=key.get_key())
    messages = [SystemMessage(prompt['normal_answer'])] + state["messages"] + [HumanMessage(f"Tên phụ huynh: {state.parent_name}")]
    result = await llm.ainvoke(messages)
    return {"messages": [result.content]}

async def get_age_group_children_router(state: State):
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=key.get_key())
    messages = [SystemMessage(prompt['get_age_group_children_router'])] + state["messages"]
    result = await llm.ainvoke(messages)

    result = "optimize" if result.content == "optimize" else "ask"
    return {"decision": result}

async def get_age_group_children_decision(state: State):
    return "ask" if state['decision'] == "ask" else "optimize"

async def ask_age_group_children(state: State):
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=key.get_key())
    messages = [SystemMessage(prompt['ask_age_group_children'])] + state["messages"] + [HumanMessage(f"Tên phụ huynh: {state.parent_name}")]
    result = await llm.ainvoke(messages)

    return {"messages": result.content}

async def optimize_query(state: State):
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=key.get_key())
    messages = [SystemMessage(prompt['optimize_query'])] + state["messages"] + [HumanMessage(f"Tên phụ huynh: {state.parent_name}")]
    result = await llm.ainvoke(messages)

    return {"query": result.content}

async def retrieve_info(state: State):
    result = []
    return {"info": result}

async def answer_with_info(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


#add node
graph_builder.add_node("llm_router", llm_router)
graph_builder.add_edge(START, "llm_router")
graph_builder.add_node("normal_answer", normal_answer)
graph_builder.add_node("get_age_group_children_router", get_age_group_children_router)
graph_builder.add_node("ask_age_group_children", ask_age_group_children)
graph_builder.add_node("optimize_query", optimize_query)
graph_builder.add_node("retrieve_info", retrieve_info)
graph_builder.add_node("answer_with_info", answer_with_info)

#condition
graph_builder.add_conditional_edges("llm_router", llm_decision, {"normal": "normal_answer", "retrieval": "get_age_group_children_router"})
graph_builder.add_conditional_edges("get_age_group_children_router", get_age_group_children_decision, {"ask": "ask_age_group_children", "optimize": "optimize_query"})

#add edges
graph_builder.add_edge("optimize_query", "retrieve_info")
graph_builder.add_edge('retrieve_info', 'answer_with_info')

#finish
graph_builder.add_edge("normal_answer", END)
graph_builder.add_edge("ask_age_group_children", END)
graph_builder.add_edge("answer_with_info", END)

graph = graph_builder.compile()
with open("graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())
