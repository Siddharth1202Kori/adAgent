import os
import functools
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

load_dotenv()


class MistralEmbeddings(Embeddings):
    """Custom LangChain-compatible embeddings wrapper for Mistral's API."""

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("MISTRAL_API_KEY"),
            base_url="https://api.mistral.ai/v1",
        )
        self.model = "mistral-embed"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.model,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=[text],
            model=self.model,
        )
        return response.data[0].embedding


class CRO_RAG:
    def __init__(self, index_path="cro_faiss_index"):
        self.embeddings = MistralEmbeddings()
        self.index_path = index_path
        self.vector_store = None
        self._initialize_or_load()

    def _initialize_or_load(self):
        if os.path.exists(self.index_path):
            self.vector_store = FAISS.load_local(
                self.index_path, self.embeddings, allow_dangerous_deserialization=True
            )
        else:
            initial_docs = [
                Document(
                    page_content="AIDA Framework: Attention, Interest, Desire, Action. Get attention with the headline, build interest with features, create desire with benefits, prompt action with CTA.",
                    metadata={"source": "AIDA"},
                ),
                Document(
                    page_content="PAS Framework: Problem, Agitation, Solution. Identify the problem, agitate it by showing consequences, and present the product as the solution.",
                    metadata={"source": "PAS"},
                ),
                Document(
                    page_content="Message Match: The ad and the landing page should have exact or very close message match. If the ad promises X, the landing page hero section must deliver X immediately.",
                    metadata={"source": "Message Match"},
                ),
                Document(
                    page_content="Clarity over Cleverness: Ensure the value proposition is immediately clear. Avoid clever buzzwords if they confuse the user.",
                    metadata={"source": "Clarity"},
                ),
                Document(
                    page_content="Social Proof: Include testimonials, logos, and success metrics to build trust with the visitor.",
                    metadata={"source": "Trust"},
                ),
            ]
            self.vector_store = FAISS.from_documents(initial_docs, self.embeddings)
            self.vector_store.save_local(self.index_path)

    def retrieve(self, query: str, k: int = 3):
        if not self.vector_store:
            return []
        docs = self.vector_store.similarity_search(query, k=k)
        return docs


@functools.lru_cache(maxsize=32)
def get_rag_context(query: str, k: int = 3) -> str:
    rag = CRO_RAG()
    docs = rag.retrieve(query, k=k)
    return "\n\n".join([d.page_content for d in docs])
