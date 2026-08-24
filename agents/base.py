"""Infraestrutura compartilhada para os agentes do pipeline.

Define o estado e o grafo LangGraph utilizados por todos os agentes:
o nó ``agent`` consulta o modelo, que pode solicitar ferramentas; o nó
``tools`` executa as ferramentas e devolve o resultado ao modelo até
haver uma resposta final.
"""

import json
import operator
import os
from pathlib import Path
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from dotenv import load_dotenv


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


def load_chat_model() -> ChatOpenAI:
    """Cria o modelo de chat padrão do projeto a partir do .env."""
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    return ChatOpenAI(
        temperature=0,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )


def extrair_parametros(
    schema: type[BaseModel],
    instrucao: str,
    mensagem_usuario: str,
):
    """Extrai parâmetros estruturados da mensagem do usuário via structured output."""
    chain = load_chat_model().with_structured_output(schema)
    prompt = f"{instrucao}\n\nMensagem do usuário: {mensagem_usuario}"
    return chain.invoke([HumanMessage(content=prompt)])


class Agent:
    """Orquestra um modelo LangChain e tools por meio de um grafo LangGraph."""

    def __init__(self, model, tools, system: str = ""):
        self.system = system
        self.tools = {tool.name: tool for tool in tools}
        self.model = model.bind_tools(tools)

        graph = StateGraph(AgentState)
        graph.add_node("agent", self.call_model)
        graph.add_node("tools", self.take_action)
        graph.set_entry_point("agent")
        graph.add_conditional_edges(
            "agent", self.has_tool_calls, {True: "tools", False: END}
        )
        graph.add_edge("tools", "agent")
        self.graph = graph.compile()

    def has_tool_calls(self, state: AgentState) -> bool:
        return bool(getattr(state["messages"][-1], "tool_calls", []))

    def call_model(self, state: AgentState):
        messages = state["messages"]
        if self.system:
            messages = [SystemMessage(content=self.system), *messages]
        return {"messages": [self.model.invoke(messages)]}

    def take_action(self, state: AgentState):
        results = []
        for tool_call in state["messages"][-1].tool_calls:
            print(
                f"Ferramenta '{tool_call['name']}' chamada "
                f"com os argumentos: {tool_call['args']}"
            )
            tool = self.tools.get(tool_call["name"])
            if tool is None:
                result = {"erro": f"Tool inexistente: {tool_call['name']}"}
            else:
                try:
                    result = tool.invoke(tool_call["args"])
                except Exception as exc:
                    result = {"erro": str(exc)}

            results.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"],
                    content=json.dumps(result, ensure_ascii=False, default=str),
                )
            )
        return {"messages": results}

    def invoke(self, pergunta: str):
        return self.graph.invoke({"messages": [HumanMessage(content=pergunta)]})
