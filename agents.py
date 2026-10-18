from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv
import os
load_dotenv()

# Model setup: Groq is the default; Ollama is optional for local development.
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is missing. Set it in your environment.")
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            api_key=api_key,
            temperature=0,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {provider}. Choose 'groq' or 'ollama'."
    )


llm = get_llm()

#1st agent
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search]
    )

#2nd agent
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url]
    )


#write chain

# writer_prompt = ChatPromptTemplate.from_messages([ 

#     ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
#     ("human", """Write a detailed research report on the topic below.

#     Topic: {topic}

#     Research Gathered:
#     {research}

#     Structure the report as:
#     - Introduction
#     - Key Findings (minimum 3 well-explained points)
#     - Conclusion
#     - Sources (list all URLs found in the research)

#     Be detailed, factual and professional."""),

# ])



#write chain (Advanced version with detailed instructions)
writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a professional research writer and analytical expert.
        Your responsibility is to transform gathered research into a comprehensive,
        accurate, evidence-based, and professionally structured research report.

        Follow these principles:
        - Maintain an objective, formal, and professional tone.
        - Present information logically, using clear headings and subheadings.
        - Support key claims with evidence from the provided research.
        - Distinguish verified facts from opinions, interpretations, and uncertainties.
        - Analyze findings rather than simply summarizing information.
        - Avoid repetition, unsupported claims, fabricated statistics, and invented sources.
        - Use bullet points, numbered lists, and tables when they improve readability.
        - Include relevant dates, statistics, examples, and comparisons when available.
        - Cite sources using URLs provided in the gathered research.
        - If information is insufficient, explicitly acknowledge the limitation.
        - Never invent references, quotations, or research findings."""
    ),
    (
        "human",
        """Write a detailed, professional research report on the following topic.

        Topic: {topic}

        Research Gathered:
        {research}

        Follow this report structure:

        1. Title
           - Create a clear, descriptive, and professional title.

        2. Executive Summary
           - Summarize the research objective, major findings, and overall conclusion.
           - Highlight the most important insights concisely.

        3. Introduction
           - Introduce the topic and its background.
           - Explain the purpose and scope of the research.
           - Describe why the topic is important.

        4. Research Methodology
           - Briefly explain how the gathered research informs the report.
           - Identify the types of evidence and sources available.
           - Mention any limitations in the available research.
           - Do not claim that research methods were used unless supported
             by the provided research.

        5. Key Findings and Analysis
           - Present at least 3 substantial findings, each with a descriptive
             subheading.
           - Explain each finding in detail, including relevant facts,
             statistics, examples, trends, and comparisons when available.
           - Analyze the significance and implications of each finding.
           - Support factual claims with relevant source URLs.
           - Explain conflicting evidence or differing perspectives when present.
           - Do not repeat the same information across multiple findings.

        6. Implications and Recommendations
           - Explain the practical implications of the findings.
           - Provide actionable, evidence-based recommendations where appropriate.
           - Clearly distinguish recommendations from established facts.

        7. Research Limitations
           - Identify gaps, uncertainties, source limitations, or conflicting
             information that could affect the conclusions.
           - Do not invent limitations that are not reasonably supported.

        8. Conclusion
           - Summarize the most important findings.
           - Answer the central research question using the available evidence.
           - Present a balanced final assessment without introducing
             unsupported new information.

        9. Sources and References
           - List all unique URLs found in the provided research.
           - Include source titles or website names when available.
           - Prefer a numbered list for readability.
           - Link claims to relevant sources wherever possible.
           - Do not fabricate URLs, titles, authors, publication dates,
             or references.
           - If no URLs are available, explicitly state that no source URLs
             were provided in the gathered research.

        Writing and formatting requirements:
        - Use professional report-style Markdown formatting.
        - Use clear headings, meaningful subheadings, and readable paragraphs.
        - Ensure the report is detailed, coherent, factual, and analytical.
        - Explain technical terminology when necessary for the intended reader.
        - Avoid unnecessary jargon, repetition, exaggerated claims, and filler.
        - Base the report exclusively on the gathered research and clearly
          identify any information gaps.
        - Ensure every major section contributes meaningful information.

        Produce the complete report, not an outline or a list of writing
        instructions."""
    ),
])



writer_chain = writer_prompt | llm | StrOutputParser()

#critic_chain
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),

])

critic_chain = critic_prompt | llm | StrOutputParser()