from functools import partial
import operator
from typing import Annotated, Any, NotRequired, Optional, Sequence, TypedDict, cast
from dotenv import load_dotenv
import os
import logging
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.schemas.ai_schemas import StateAnalysis
from app.services.exercise_service import EXERCISE_SERVICE
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vector_service import VECTOR_SERVICE
from langchain_core.utils.utils import convert_to_secret_str

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Attention: OPENAI_API_KEY was not found in .env file!")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise RuntimeError("Attention: OPENAI_API_KEY was not found in .env file!")


# Das schlaue Gehirn für die Analyse (Check-Up & Zusammenfassung)
logic_model = ChatOpenAI(temperature=0.1, model="gpt-4.1-mini", api_key=convert_to_secret_str(OPENAI_API_KEY))  # type: ignore
# Das empathische Gehirn für den Chat (günstig)
chat_model = ChatOpenAI(
    temperature=0.8, model="gpt-4o-mini", api_key=convert_to_secret_str(OPENAI_API_KEY)
)


tavily = TavilySearch(api_key=convert_to_secret_str(TAVILY_API_KEY), max_results=5)
tools = [tavily]
# Das Logik-Modell braucht Zugriff auf die Tools
logic_model_with_tools = logic_model.bind_tools(tools)

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_id: str
    is_user_ready: NotRequired[bool]
    is_exercise_useful: NotRequired[bool]
    has_enough_info: NotRequired[bool]
    needs_research: NotRequired[bool]
    is_in_exercise: NotRequired[bool]
    exercise_goal: NotRequired[Optional[str]]
    exercise_expertise: NotRequired[Optional[str]]
    exercise_instructions: NotRequired[Optional[str]]
    exercise_id: NotRequired[Optional[int]]
    user_data: NotRequired[dict]
    memory_results: NotRequired[list[str]]


def doorman(state: AgentState):
    print("--- DOORMAN ---")
    if state.get("is_in_exercise"):
        return "get_user_memory"
    return "check_user_state"


async def check_user_state(state: AgentState):
    print("--- CHECK USER STATE ---")
    user_data = state.get("user_data", {})
    user_context = create_user_context(user_data)
    system_prompt = f"""
    Du bist die Analyse-Einheit von Serenity. 
    {user_context}
    Analysiere den Chatverlauf und entscheide präzise über die nächsten Schritte.
    Nutze das Onboarding-Wissen, um zu beurteilen, ob wir genug Infos haben. 
    Wenn der User explizit nach einer Übung fragt, dann gib ihm auch eine, wenn du genügend Infos über ihn hast.
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
    print("--- DECISION MAKER ---")
    if state.get("needs_research", False):
        return "web_search"  # node
    if (
        state.get("is_user_ready", False)
        and state.get("is_exercise_useful", False)
        and state.get("has_enough_info", False)
    ):
        return "get_matching_exercise"  # node
    return "get_user_memory"


async def get_matching_exercise(state: AgentState):
    print("--- NODE: FIND EXERCISE ---")
    user_summary = f"""
        DU BIST EIN NEUTRALER ANALYTIKER FÜR EMOTIONALE VEKTOREN.
        Deine Aufgabe: Extrahiere Keywords für eine Datenbank-Suche basierend NUR auf dem aktuellen User-Zustand.
        SCHRITT 1: Energie-Check (Interner Prozess):
        - Ist die Energie HOCH (Wut, Panik, Drang)? -> Nutze Begriffe für Entladung.
        - Ist die Energie NIEDRIG (Trauer, Leere, Erschöpfung)? -> Nutze Begriffe für Nährung/Halt.
        SCHRITT 2: Keyword-Ausgabe (KEINE SÄTZE):
        1. INDIKATION:
        [Nur Fachbegriffe, die zur aktuellen Energie passen. Bei Trauer z.B.: Hypoarousal, depressive Dynamik, Rückzug, Schwere.]
        2. USER-ERLEBEN:
        [Nutze NUR Begriffe, die der User wirklich gesagt hat oder die direkt dazu passen. Bei Trauer z.B.: weinen, hoffnungslos, traurig, leer.]
        3. FUNKTION:
        [Was braucht das System jetzt? Bei Trauer z.B.: Trost, Stabilisierung, sanfte Aktivierung, emotionaler Raum.]
        WICHTIG: Nutze niemals Begriffe wie "Aggression" oder "Schlagen", wenn der User traurig ist. Nutze niemals "Ruhe", wenn der User explodieren will.
    """
    response = await logic_model.ainvoke(
        [SystemMessage(content=user_summary)] + list(state["messages"])
    )

    summary_text = str(response.content)
    print(f"Zusammenfassung für chroma: {summary_text}")
    exercise_id = await VECTOR_SERVICE.search_exercise(summary_text)
    return {
        "exercise_id": exercise_id,
    }


async def get_exercise_from_db(state: AgentState, db: AsyncSession):
    print("--- NODE: GET EXERCISE DETAILS ---")
    exercise_id = state.get("exercise_id")
    if not exercise_id:
        print("No exercise from chroma")
        return {}
    exercise = await EXERCISE_SERVICE.get_exercise_by_id(db, exercise_id)
    if not exercise:
        logger.warning(f"No exercise with id {exercise_id} in database")
        return {}
    return {
        "is_in_exercise": True,
        "exercise_goal": exercise.goal,
        "exercise_expertise": exercise.expertise,
        "exercise_instructions": exercise.instructions,
    }


async def get_user_memory(state: AgentState):
    print("--- NODE: GET USER MEMORY ---")
    user_id = state["user_id"]
    last_message = state["messages"][-1]
    if not isinstance(last_message, HumanMessage):
        return {}
    if len(str(last_message)) <= 15:
        return {}
    ids_to_exclude = state.get("user_data", {}).get("excluded_ids", [])
    results = await VECTOR_SERVICE.get_user_memories_for_serenity(
        user_id, str(last_message.content)
    )
    important_memory = []
    for result in results:
        doc, score = result
        if doc.metadata["id"] in ids_to_exclude:
            continue
        if score <= 0.5:
            user_memory = doc.page_content
            reasoning_list = doc.metadata.get("reasoning", [])
            if reasoning_list:
                user_memory += f"Bestätigt durch: "
                for reason in reasoning_list:
                    user_memory += f"\n - {reason}"
            important_memory.append(user_memory)
            print(f"MEMORIES: {important_memory[:3]}")
    return {"memory_results": important_memory[:3]}


async def chat_therapist(state: AgentState):
    print("--- YOUR THERAPIST IS TALKING ---")
    user_data = state.get("user_data", {})
    user_context = create_user_context(user_data)
    memories = state.get("memory_results", [])

    system_prompt = f"""
    Du bist Serenity, der „Archetypische Metaphern-Coach“ – eine einfühlsame, präsente und radikal loyale Begleiterin für Persönlichkeitsentwicklung. 
    Dein Grundstil ist kraftvoll, strukturiert und empathisch.
    WICHTIGSTE PRIORITÄT (USER-KONTEXT & MERKMALE):
    Hier sind die fixen Daten des Users (inklusive Geschlecht für Grammatik und Spitznamen):
    {user_context}"""
    if memories:
        system_prompt += "\n\nZUSÄTZLICHER KONTEXT & AKTUELLES THEMA:"
        for memory in memories:
            system_prompt += f"\n- {memory}"
    system_prompt += f"""
        

    DEIN DIALOG-VERHALTEN (SITUATIV & FLEXIBEL):
    1. DER USER STEHT IM FOKUS: Reagiere immer individuell auf das, was der User im aktuellen Moment braucht. Deine absolute Hauptaufgabe ist es, zuzuhören, Gefühle messerscharf zu SPIEGELN und dem User das Gefühl zu geben, vollkommen verstanden und sicher zu sein.
    2. METAPHERN ALS GEWÜRZ: Nutze lebendige Alltags-Metaphern (Haus, Akku, Kompass), wenn sie dem User helfen, sein Chaos besser zu verstehen. Wenn der User stark emotional oder verzweifelt ist, lass die Metaphern komplett weg und sei einfach nur menschlicher Halt.
    3. PEPP & SPITZNAMEN: Bring eine motivierende, frische Energie in das Gespräch, sobald der User bereit dafür ist. Du darfst ihm ab und zu stärkende, zum Geschlecht passende Spitznamen geben (Frau: Königin, Hüterin / Mann: König, Hüter). Nutze sie aber niemals am Satzanfang und niemals inflationär, sondern nur als seltenes, kraftvolles Highlight. Nutze niemals "Kapitän".
    4. KEINE ZWANGS-PLÄNE: Plane nichts voraus und erstelle keine To-Do-Listen. 
    STIL & FORMAT:
    - Antworte extrem kurz und knackig (maximal 50-60 Wörter).
    - Nutze Markdown (Fettdruck für emotionale Anker, Absätze für Struktur).
    
     """

    if state.get("is_in_exercise"):
        instructions = state.get("exercise_instructions")
        if instructions:
            system_prompt += f"""
            AKTUELL: Deine Übung hat das Ziel '{state.get('exercise_goal')}'.
            HINTERGRUND: {state.get('exercise_expertise')}
            DEINE ANLEITUNG: {state.get('exercise_instructions')}
            AUFGABE: Begleite den User Schritt für Schritt durch diese Übung. Passe die Übung auf seine Situation an, 
            auch wenn sie dann länger dauert. 
            Wenn die Übung beendet ist, frage: 'Wie geht es dir jetzt? Hat dir diese Übung geholfen'
            ENDE DER KOMPLETTEN ÜBUNG: Setze das Signal [FINISHED] ans Ende deiner Antwort."""

    # Nachrichtenliste für KI zusammen bauen
    # System-Prompt und hängen den bisherigen Chatverlauf an
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    # 4. Wir rufen das günstige chat_model (GPT-4o-mini) auf
    response = await chat_model.ainvoke(messages)

    if not state.get("is_in_exercise"):
        return {"messages": [response]}
    last_ai_text = str(response.content)
    exercise_finished = "[FINISHED]" in last_ai_text
    print(f"--- FINISHED ---: {exercise_finished}")
    ai_text_for_user = last_ai_text.replace("[FINISHED]", "").strip()
    return {
        "messages": [AIMessage(content=ai_text_for_user)],
        "is_in_exercise": not exercise_finished,
        "exercise_id": None if exercise_finished else state.get("exercise_id"),
    }


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


def create_serenity_core_agent(
    db: AsyncSession,
):
    # Graph wird initialisiert
    workflow = StateGraph(AgentState)

    # Nodes zum Graphen hinzufügen, mit partial werden die argumente hinzugefügt - workflow.add_node("name", function)
    workflow.add_node("check_user_state", check_user_state)
    workflow.add_node("web_search", web_search)
    workflow.add_node("get_matching_exercise", get_matching_exercise)
    workflow.add_node("get_exercise_from_db", partial(get_exercise_from_db, db=db))
    workflow.add_node("get_user_memory", get_user_memory)
    workflow.add_node("chat_therapist", chat_therapist)

    # workflow.set_contional_entry_point(function, {"return value der funktion": "name aus workflow.add()"})
    workflow.set_conditional_entry_point(
        doorman,
        {
            # links: return wert aus doorman(), rechts: "name" aus workflow.add()
            "get_user_memory": "get_user_memory",
            "check_user_state": "check_user_state",
        },
    )
    workflow.add_conditional_edges(
        "check_user_state",  # von welcher funktion kommen wir?
        decision_after_check,
        {  # funktion, die entscheidet
            "web_search": "web_search",  # MEntscheidungsmöglichkeiten
            "get_matching_exercise": "get_matching_exercise",
            "get_user_memory": "get_user_memory",
        },
    )

    workflow.add_edge("web_search", "chat_therapist")
    workflow.add_edge("get_matching_exercise", "get_exercise_from_db")
    workflow.add_edge("get_exercise_from_db", "chat_therapist")
    workflow.add_edge("get_user_memory", "chat_therapist")
    workflow.add_edge("chat_therapist", END)

    return workflow.compile(checkpointer=state_memory)


def create_user_context(user_data: dict[str, Any]):
    user_context = f"""
         Der User ist {user_data.get("nickname", "Du")}"""
    if user_data.get("gender"):
        user_context = f"{user_data["gender"]}"
    if user_data.get("age"):
        user_context = f"und {user_data["age"]} Jahre alt."
    if user_data.get("safe_place"):
        user_context += f"\nSein Wohlfühlort ist {user_data['safe_place']}."
    if user_data.get("situation"):
        user_context += (
            f"\nSeine aktuelle Lebenssituation ist: {user_data['situation']}."
        )
