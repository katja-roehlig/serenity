from functools import partial
import operator
from typing import Annotated, NotRequired, Optional, Sequence, TypedDict, cast
from dotenv import load_dotenv
import os
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# from langgraph.prebuilt import ToolNode, tools_condition
# from openai import api_key
from pydantic import BaseModel, Field
from app.services.exercise_service import EXERCISE_SERVICE
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vector_service import VECTOR_SERVICE

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Attention: OPENAI_API_KEY was not found in .env file!")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise RuntimeError("Attention: OPENAI_API_KEY was not found in .env file!")


# Das schlaue Gehirn für die Analyse (Check-Up & Zusammenfassung)
logic_model = ChatOpenAI(temperature=0.2, model="gpt-4.1-mini", api_key=OPENAI_API_KEY)  # type: ignore
# Das empathische Gehirn für den Chat (günstig)
chat_model = ChatOpenAI(temperature=0.8, model="gpt-4o-mini", api_key=OPENAI_API_KEY)  # type: ignore


tavily = TavilySearch(api_key=TAVILY_API_KEY, max_results=5)
tools = [tavily]
# Das Logik-Modell braucht Zugriff auf die Tools
logic_model_with_tools = logic_model.bind_tools(tools)


# state wird erfasst
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    is_user_ready: NotRequired[bool]
    is_exercise_useful: NotRequired[bool]
    has_enough_info: NotRequired[bool]
    needs_research: NotRequired[bool]
    is_in_exercise: NotRequired[bool]
    exercise_title: NotRequired[Optional[str]]
    exercise_content: NotRequired[Optional[str]]
    exercise_instructions: NotRequired[Optional[str]]
    exercise_id: NotRequired[Optional[str]]


class StateAnalysis(BaseModel):
    is_user_ready: bool = Field(
        description="Can the user physically/mentally perform an exercise right now?"
    )
    is_exercise_useful: bool = Field(
        description="Is an exercise better than just talking right now?"
    )
    has_enough_info: bool = Field(
        description="True ONLY if the user has provided enough context to select a SPECIFIC exercise. If the user is vague (e.g., 'I feel bad'), set to False so we can ask clarifying questions first."
    )
    needs_research: bool = Field(
        description="Do we need to search the web to understand a term or situation?"
    )


def doorman(state: AgentState):
    if state.get("is_in_exercise"):
        return "chat_therapist"
    return "check_user_state"


async def check_user_state(state: AgentState, user: dict):

    system_prompt = f"""
    Du bist die Analyse-Einheit von Serenity. Dein User ist {user['nickname']}.
    Stärken: {user['strengths']}. Sicherer Ort: {user['safe_place']}.
    
    Analysiere den Chatverlauf und entscheide präzise über die nächsten Schritte.
    Nutze das Onboarding-Wissen, um zu beurteilen, ob wir genug Infos haben.
    """

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    # Das Modell wird angewiesen, das StateAnalysis-Schema auszufüllen
    structured_llm = logic_model.with_structured_output(StateAnalysis)

    # Daten werden zu KI geschickt und ausgefühlt in einem ai_result-Objekt zurückgegeben
    ai_result = cast(StateAnalysis, await structured_llm.ainvoke(messages))
    # Wir geben die Ergebnisse zurück, um die Akte (State) zu aktualisieren
    return {
        "is_user_ready": ai_result.is_user_ready,
        "is_exercise_useful": ai_result.is_exercise_useful,
        "has_enough_info": ai_result.has_enough_info,
        "needs_research": ai_result.needs_research,
    }


def decision_after_check(state: AgentState):
    if state.get("needs_research", False):
        return "web_search"  # node
    if (
        state.get("is_user_ready", False)
        and state.get("is_exercise_useful", False)
        and state.get("has_enough_info", False)
    ):
        return "get_matching_exercise"  # node
    return "chat_therapist"


async def get_matching_exercise(state: AgentState):
    print("--- NODE: FIND EXERCISE ---")
    user_summary = (
        "DU BIST EIN INTERNER DATEN-ANALYTIKER."
        "Du erstellst eine Zusammenfassung für eine Datenbank-Suche (ChromaDB)"
        "Fasse den emotionalen Zustand des Users und sein Kernproblem zusammen. "
        "WICHTIG: Nutze maximal 2 bis 3 kurze Sätze (ca. 30-40 Wörter)."
        "Nutze die Sprache des Users. Ziel: eine passende Übung finden."
    )
    response = await logic_model.ainvoke(
        [SystemMessage(content=user_summary)] + list(state["messages"])
    )

    summary_text = str(response.content)
    print(f"Zusammenfassung für chroma: {summary_text}")
    exercise_id = await VECTOR_SERVICE.search_exercise(summary_text)
    return {"exercise_id": exercise_id}


async def get_exercise_from_db(state: AgentState, db: AsyncSession):
    print("--- NODE: GET EXERCISE DETAILS ---")
    exercise_id = state.get("exercise_id")
    if not exercise_id:
        print("No exercise from chroma")
        return {}
    exercise = await EXERCISE_SERVICE.get_exercise_by_id(db, exercise_id)
    if not exercise:
        print(f"No exercise with id {exercise_id} in database")
        return {}
    return {
        "exercise_title": exercise.title,
        "exercise_content": exercise.content,
        "exercise_instructions": exercise.instructions,
        "is_in_exercise": True,
    }


async def chat_therapist(state: AgentState, user: dict):
    print("Your therapist is talking")
    system_prompt = f"""
        Du bist Serenity, ein erfahrener und einfühlsamer Therapeut.
        Antworte extrem kurz und knackig. Verwende maximal 50-60 Wörter. 
        Dein Client ist {user["nickname"]}, {user["gender"]} und {user["age"]} Jahre alt.
        Sein Wohlfühlort ist {user["safe_place"]} und er zu seinen Stärken zählen: {user["strengths"]}.
        DEINE MISSION:
            1. Sei empathisch. Wenn der User leidet, validiere zuerst seine Gefühle (z.B. 'Das ist echt verdammt hart, dass du den Job verloren hast').
            2. Nutze die Stärken NIEMALS als Floskel. 
            3. Biete den Wohlfühlort oder die Stärken nur als OPTION an, wenn der User nach Bewältigungsstrategien sucht oder völlig blockiert ist. 
            4. Wenn der User einen Vorschlag ablehnt, akzeptiere das sofort und bohre nicht nach.
     """
    if state.get("is_in_exercise"):
        system_prompt += f"""
        AKTUELL: Du führst die Übung '{state.get('exercise_title')}' durch.
        HINTERGRUND: {state.get('exercise_content')}
        DEINE ANLEITUNG: {state.get('exercise_instructions')}
        Wenn keine Übung findest, erstelle eine, die gut auf den user zugeschnitten ist und ihm hilft, sich besser zu fühlen.
        AUFGABE: Begleite den User Schritt für Schritt durch diese Übung. 
        Wenn die Übung beendet ist, frage: 'Wie geht es dir jetzt?'
        """
    # Nachrichtenliste für KI zusammen bauen
    # System-Prompt und hängen den bisherigen Chatverlauf an
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    # 4. Wir rufen das günstige chat_model (GPT-4o-mini) auf
    response = await chat_model.ainvoke(messages)
    # Wir geben die Antwort der KI zurück in die Akte (State)
    return {"messages": [response]}


async def web_search(state: AgentState):
    print("--- NODE: WEB SEARCH ----")
    last_user_message = state.get("messages")[-1].content
    if not isinstance(last_user_message, str):
        return {}
    search_query = last_user_message.strip()
    if not search_query:
        return {}
    search_results = await tavily.ainvoke(search_query)
    new_ai_knowledge = SystemMessage(content=f"background: {search_results}")
    return {"messages": [new_ai_knowledge], "needs_research": False}


state_memory = MemorySaver()


def create_serenity_core_agent(db_session, user_data: dict):
    # Graph wird initialisiert
    workflow = StateGraph(AgentState)

    # Nodes zum Graphen hinzufügen, mit partial werden die argumente hinzugefügt - workflow.add_node("name", function)
    workflow.add_node("check_user_state", partial(check_user_state, user=user_data))
    workflow.add_node("web_search", web_search)
    workflow.add_node("get_matching_exercise", get_matching_exercise)
    workflow.add_node(
        "get_exercise_from_db", partial(get_exercise_from_db, db=db_session)
    )
    workflow.add_node("chat_therapist", partial(chat_therapist, user=user_data))

    # workflow.set_contional_entry_point(function, {"return value der funktion": "name aus workflow.add()"})
    workflow.set_conditional_entry_point(
        doorman,
        {
            # links: return wert aus doorman(), rechts: "name" aus workflow.add()
            "chat_therapist": "chat_therapist",
            "check_user_state": "check_user_state",
        },
    )

    workflow.add_conditional_edges(
        "check_user_state",  # von welcher funktion kommen wir?
        decision_after_check,
        {  # funktion, die entscheidet
            "web-search": "web_search",  # MEntscheidungsmöglichkeiten
            "get_matching_exercise": "get_matching_exercise",
            "chat_therapist": "chat_therapist",
        },
    )

    workflow.add_edge("web_search", "chat_therapist")
    workflow.add_edge("get_matching_exercise", "get_exercise_from_db")
    workflow.add_edge("get_exercise_from_db", "chat_therapist")
    workflow.add_edge("chat_therapist", END)

    return workflow.compile(checkpointer=state_memory)


# hier werden die nodes erstellt
# workflow.add_node("search", tool_node)
# workflow.add_node("llm", call_model)

# edges hinzufügen
# workflow.set_entry_point("llm")  # name vom eingangspunkt

# workflow.add_edge("search", "llm")  # von search (=start) nach llm (=ziel)
# workflow.add_conditional_edges(
#     "llm",
#     tools_condition,
# )

# app = workflow.compile()

# app.get_graph().print_ascii()

# if __name__ == "__main__":
#     user_prompt = input("Was ist deine Frage? ")
#     initial_state = {
#         "messages": [
# SystemMessage(content="Führe immer mindestens eine Suche aus"),
#         HumanMessage(content=user_prompt)
#     ]
# }

# app.invoke(initial_state) #normale function

# ausführliche anzeige
# for output in app.stream(initial_state):
#     for key, value in output.items():
#         print(f"Output from node {key}")
#         print("---")
#         for message in value["messages"]:
#             message.pretty_print()
#             print("\n---\n")

# jede node muss eine funktion sein = AgentCore
# def call_model(state: AgentState):
#     print("Call AgentCore")
#     messages = state["messages"]
# nachricht wird ans llm geschickt
# response = logic_model_with_tools.invoke(messages)
# return {"messages": [response]}
# verwandelt all meine tools in nodes
# tool_node = ToolNode(tools)
