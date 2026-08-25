"""Ponto de entrada interativo do Projeto IA para Produtividade.

Executa sem parâmetros, apresenta um resumo do projeto e aguarda o
pedido do usuário, que é processado pelo Agente Orquestrador.
"""

import sys

from agents.agent_orchestrator import build_orchestrator

RESUMO = """
==============================================
 🤖 Projeto IA para Produtividade
==============================================
Pipeline multi-agente que transforma conversas,
reuniões ou pedidos em tarefas organizadas e
executáveis.

Agentes implementados:
 - Agente Orquestrador : delega o pedido aos especialistas
 - Agente Transcrição  : limpa a conversa e estrutura o briefing
 - Agente Agile Coach  : gera épicos, histórias e subtasks
 - Agente GitHub       : cria e organiza Issues no Project/Kanban
 - Agente Slack        : comunica a equipe com um resumo final

Fluxo:
 você descreve o pedido
   -> orquestrador aciona os especialistas
   -> transcrição limpa a conversa (se houver)
   -> agile coach estrutura o backlog
   -> ações executadas no GitHub
   -> resumo enviado ao Slack
==============================================
"""


def main() -> None:
    print(RESUMO)

    print("Carregando agentes...")
    orchestrator = build_orchestrator()
    print("Pronto!\n")

    while True:
        try:
            pedido = input("Descreva o que deve ser feito (enter vazio para sair): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando.")
            break

        if not pedido:
            print("Encerrando.")
            break

        print("\nProcessando...\n")
        try:
            resultado = orchestrator.invoke(pedido)
        except Exception as exc:
            print(f"[ERRO] {exc}\n")
            continue

        print(resultado["messages"][-1].content)
        print()


if __name__ == "__main__":
    sys.exit(main())
