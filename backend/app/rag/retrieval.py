from typing import List, AsyncGenerator
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.prompts import PromptTemplate
from flashrank import Ranker, RerankRequest
import json

from app.core.config import settings
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize Reranker (Lazy)
def get_ranker():
    try:
        return Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/app/.cache")
    except Exception as e:
        print(f"Failed to load Ranker: {e}")
        return None

# Initialize Web Search (Lazy)
# Initialize Web Search (Lazy)
def get_web_search():
    try:
        return DuckDuckGoSearchRun()
    except Exception as e:
        print(f"Failed to load Web Search: {e}")
        return None

# Initialize LLM (Lazy or safe global? ChatOpenAI usually safe but let's be consistent)
# Actually ChatOpenAI is lightweight config. Keep global or lazy. Let's keep global for now to avoid re-init overhead if not needed.
llm = ChatOpenAI(
    model_name="gpt-4o", # Using 4o as per plan
    temperature=0,
    openai_api_key=settings.OPENAI_API_KEY,
    streaming=True
)

# Initialize Cache Store (Lazy load inside function or here but protected)
import chromadb
from app.rag.ingestion import get_vector_store

def get_cache_store():
    # Reuse client logic roughly or new (Chroma HTTP client is thread safe usually)
    chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    return Chroma(
        collection_name="semantic_cache",
        embedding_function=OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY, model="text-embedding-3-small"),
        client=chroma_client
    )

CACHE_THRESHOLD = 0.90

CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template("""Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:""")

QA_PROMPT = PromptTemplate.from_template("""You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Helpful Answer:""")

class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self, queue):
        self.queue = queue

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.queue.put_nowait(token)

async def chat_stream(
    question: str,
    chat_history: List[tuple],
):
    # Lazy Init
    vector_store = get_vector_store()
    cache_store = get_cache_store()
    ranker = get_ranker()
    web_search = get_web_search()

    # 0. Check Semantic Cache
    try:
        # Search properly for 1 nearest neighbor
        cached_docs = await cache_store.asimilarity_search_with_relevance_scores(question, k=1)
        if cached_docs:
            doc, score = cached_docs[0]
            if score > CACHE_THRESHOLD:
                # HIT! Yield cached answer
                # Yield dummy source to keep frontend happy
                yield json.dumps({"type": "sources", "data": ["Semantic Cache"]}) + "\n\n"
                yield doc.metadata.get("answer", "")
                return
    except Exception as e:
        print(f"Cache Error: {e}")

    # 1. Retrieve initial candidates (Top 20)
    retriever = vector_store.as_retriever(search_kwargs={"k": 20})
    
    # 2. Condense Question
    standalone_question = question
    if chat_history:
        history_str = "\n".join([f"User: {h[0]}\nAssistant: {h[1]}" for h in chat_history])
        chain = CONDENSE_QUESTION_PROMPT | llm
        response = await chain.ainvoke({"chat_history": history_str, "question": question})
        standalone_question = response.content

    # 3. Get Context & Rerank
    docs = await retriever.ainvoke(standalone_question)
    
    # Rerank with FlashRank
    passages = [
        {"id": str(i), "text": doc.page_content, "meta": doc.metadata} 
        for i, doc in enumerate(docs)
    ]
    
    # Handle empty docs case
    reranked_results = []
    if passages:
        if ranker:
            try:
                 rerank_request = RerankRequest(query=standalone_question, passages=passages)
                 reranked_results = ranker.rerank(rerank_request)
            except Exception as e:
                 print(f"Rerank Error: {e}")
                 # Fallback to original docs if rerank fails (e.g. empty)
                 reranked_results = [{"text": d.page_content, "meta": d.metadata, "score": 1.0} for d in docs]
        else:
             print("Ranker not available. Skipping reranking.")
             reranked_results = [{"text": d.page_content, "meta": d.metadata, "score": 1.0} for d in docs]
    
    # Hybrid Logic: Check Relevance
    top_score = reranked_results[0]['score'] if reranked_results else 0
    use_web_search = top_score < 0.5 or not reranked_results

    sources = []
    
    
    if use_web_search:
        if web_search:
            try:
                print(f"Low relevance ({top_score:.2f}). Falling back to Web Search.")
                web_context = web_search.run(standalone_question)
                context_str = f"web_search_results:\n{web_context}"
                sources = ["DuckDuckGo Search"]
            except Exception as e:
                 # Fallback to local even if weak if web fails
                 print(f"Web Search failed: {e}")
                 if reranked_results:
                    top_docs = reranked_results[:5]
                    context_str = "\n\n".join([r["text"] for r in top_docs])
                 else:
                    context_str = "No relevant context found."
        else:
             print("Web Search not available. Skipping.")
             if reranked_results:
                top_docs = reranked_results[:5]
                context_str = "\n\n".join([r["text"] for r in top_docs])
             else:
                context_str = "No relevant context found."
    else:
        # Take top 5 local
        top_docs = reranked_results[:5]
        context_str = "\n\n".join([r["text"] for r in top_docs])
        
        # Extract Sources
        seen_sources = set()
        for r in top_docs:
            meta = r.get("meta", {})
            source_name = meta.get("source", "Unknown Document")
            if source_name not in seen_sources:
                 sources.append(source_name)
                 seen_sources.add(source_name)

    # 4. Stream Sources First (as special JSON line)
    yield json.dumps({"type": "sources", "data": sources}) + "\n\n"

    # 5. Generate Answer Stream
    if context_str == "No relevant context found.":
        # Fallback to General Chat Mode (No RAG constraints)
        print("No context found. Switching to General Chat Mode.")
        messages = [
            HumanMessage(content=standalone_question)
        ]
    else:
        # RAG Mode
        messages = [
            HumanMessage(content=QA_PROMPT.format(context=context_str, question=standalone_question))
        ]
    
    full_answer = ""
    async for chunk in llm.astream(messages):
        full_answer += chunk.content
        yield chunk.content
        
    # 6. Save to Cache
    try:
        await cache_store.aadd_documents([
            Document(page_content=standalone_question, metadata={"answer": full_answer})
        ])
    except Exception as e:
        print(f"Cache Save Error: {e}")
