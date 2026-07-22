import os
from typing import Optional

from langchain_astradb import AstraDBVectorStore
from dotenv import load_dotenv

from prod_assistant.utils.config_loader import load_config
from prod_assistant.utils.model_loader import ModelLoader

print("File is Executing")


class Retriever:
    def __init__(self):
        self.model_loader = ModelLoader()
        self.config = load_config()
        self._load_env_variables()
        self.vstore = None
        self.retriever = None
        self._init_error: Optional[str] = None

    def _load_env_variables(self):
        load_dotenv()

        required_vars = ["GOOGLE_API_KEY", "ASTRA_DB_API_ENDPOINT", "ASTRA_DB_APPLICATION_TOKEN", "ASTRA_DB_KEYSPACE"]

        missing_vars = [var for var in required_vars if os.getenv(var) is None]

        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.db_api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        self.db_application_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        self.db_keyspace = os.getenv("ASTRA_DB_KEYSPACE")

    def load_retriever(self):
        if self.retriever is not None:
            return self.retriever

        if self._init_error is not None:
            return None

        try:
            collection_name = self.config["astra_db"]["collection_name"]
            self.vstore = AstraDBVectorStore(
                embedding=self.model_loader.load_embeddings(),
                collection_name=collection_name,
                api_endpoint=self.db_api_endpoint,
                token=self.db_application_token,
                namespace=self.db_keyspace,
            )

            top_k = self.config["retriever"]["top_k"] if "retriever" in self.config else 3
            self.retriever = self.vstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": top_k,
                    "fetch_k": 20,
                    "lambda_mult": 0.7,
                    "score_threshold": 0.3,
                },
            )
            print("Retriever loaded successfully!!")
            return self.retriever
        except Exception as exc:
            self._init_error = str(exc)
            print(f"Retriever initialization failed: {exc}")
            return None

    def call_retriever(self, query):
        retriever = self.load_retriever()
        if retriever is None:
            return []
        print("Retriever Object", retriever)
        output = retriever.invoke(query)
        print("Raw output", output)
        return output


if __name__ == "__main__":
    print("Inside main block!")
    retriever_obj = Retriever()
    user_query = "can you suggest good budget laptops?"
    results = retriever_obj.call_retriever(user_query)

    for idx, doc in enumerate(results, 1):
        print(f"result {idx} : {doc.page_content} \n Metadata: {doc.metadata}")


