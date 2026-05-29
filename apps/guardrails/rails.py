import logfire
from langchain_groq import ChatGroq
from nemoguardrails import RailsConfig, LLMRails
from apps.config import settings
from apps.guardrails.colang_rules import COLANG_CONTENT,YAML_CONTENT, RAIL_INDICATORS

_rails : LLMRails | None = None

def initialize_rails():
    """
    Initializes the guardrails system with the specified rules and configuration.
    This function should be called once at the start of the application.
    """
    global _rails
    
    guard_llm = ChatGroq(
        api_key=settings.GROK_API_KEY,
        model=settings.GROQ_model,
        temperature=settings.TEMPRATURE,
    )

    config = RailsConfig.from_content(
        colang_content=COLANG_CONTENT,
        yaml_content=YAML_CONTENT,
    )

    _rails = LLMRails(config=config, llm=guard_llm)
    logfire.info("Nemoguardrails initialized with custom rules.")

    return _rails


def guard(message:str)-> tuple:
    """
    Evaluates a message against the defined guardrails and returns whether any rails were triggered.
    
    Args:
        message (str): The message to evaluate.
    """
    if _rails is None:
        logfire.warning("Guardrails not initialized. Call initialize_rails() first.")
        return False, None
    
    with logfire.span("Guardrails check"):

        result = _rails.generate(messages = [{"role":"user","content":message}])

        content = result.get("content", "") if isinstance(result, dict) else str(result)

        fired = any(indicator in content for indicator in RAIL_INDICATORS)

        if fired:
            logfire.info("Guardrail triggered for message: %s")
            return True, content
        logfire.info("No guardrails triggered for message: %s")
        return False, None

