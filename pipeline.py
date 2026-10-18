from agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

def run_research_pipeline(topic: str, progress_callback=None) -> dict:

    state = {}

    def progress(stage: str, message: str):
        if progress_callback:
            progress_callback(stage, message)

    progress("search", "Searching the web for relevant sources…")
    #search agent working 
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)


    # Step 1: Use the search agent to gather information
    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent and relevant information on the topic: {topic}")]
    })
    state['search_results'] = search_result["messages"][-1].content  # Store the search result in the state

    print("\n search result", state['search_results'])


    progress("reader", "Reading the most relevant source in depth…")
    #step 2 - reader agent 
    print("\n"+" ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"
        )]
    })

    state['scraped_content'] = reader_result['messages'][-1].content

    print("\nscraped content: \n", state['scraped_content'])

    progress("writer", "Synthesizing evidence into a structured report…")
    #step 3 - writer agent
    print("\n"+" ="*50)
    print("step 3 - Writer agent is writing a summary ...") 
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined
    })

    print("\nFinal Report:\n", state["report"])

    progress("critic", "Critiquing the report for quality and gaps…")
    #step 4 - critic report

    print("\n"+" ="*50)
    print("step 4 - Critic agent is reviewing the report ...")
    print("="*50)

    state["feedback"] = critic_chain.invoke({
        "report" : state["report"]
    })

    print("\nCritic Feedback:\n", state["feedback"])

    progress("completed", "Research and review complete.")
    return state


if __name__ == "__main__":
    topic = input("\n Enter a research topic: ")
    run_research_pipeline(topic)