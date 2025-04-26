import os
import json
import numpy as np
import faiss
import boto3
from dotenv import load_dotenv
from copy import deepcopy
from .utils import get_chatbot_response
from datetime import datetime
from difflib import get_close_matches

load_dotenv()

class DetailsAgent():
    def __init__(self):
        # Initialize chat model client
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        self.chat_model_id = os.getenv("BEDROCK_MODEL_NAME", "mistral.mistral-7b-instruct-v0:2")
        
        # Load knowledge documents directly
        self.knowledge_base = self._load_knowledge_documents(
            documents={
                "about_us": r"A:\NLP Projects\Chatbot\python_code\Experiments\Plantify_about_us.txt",
                "price_list": r"A:\NLP Projects\Chatbot\python_code\Experiments\price_list_text.txt"
            }
        )

    def _load_knowledge_documents(self, documents):
        """Load and validate knowledge documents"""
        knowledge = {}
        try:
            for doc_name, doc_path in documents.items():
                if not os.path.exists(doc_path):
                    raise FileNotFoundError(f"Document not found: {doc_path}")
                
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if not content:
                    raise ValueError(f"Empty document: {doc_path}")
                
                knowledge[doc_name] = {
                    "content": content,
                    "path": doc_path,
                    "last_modified": os.path.getmtime(doc_path)
                }
            
            print("Loaded knowledge documents:")
            for doc_name, data in knowledge.items():
                print(f"- {doc_name}: {len(data['content'])} chars, last modified {datetime.fromtimestamp(data['last_modified'])}")
            
            return knowledge
        except Exception as e:
            print(f"Failed to load knowledge base: {e}")
            raise

    def _select_relevant_documents(self, user_message):
        """Determine relevant documents with typo tolerance and context awareness"""
        try:
            if not isinstance(user_message, str) or not user_message.strip():
                return list(self.knowledge_base.keys())

            query_lower = user_message.lower()
            relevant_docs = []
            
            # Define keyword groups with common variants/typos
            price_keywords = {
                'price', 'cost', 'rate', 'pricing', 'prince', 'pice', 
                'how much', 'hw much', 'amount', '$$'
            }
            
            store_keywords = {
                'store', 'shop', 'location', 'address', 'hour', 'time', 'timing',
                'timmings', 'opening', 'close', 'deliver', 'delivery', 'about',
                'locate', 'branch', 'outlet', 'schedule', 'openhour'
            }

            # Split query into words and find close matches
            query_words = set(query_lower.split())
            threshold = 0.8  # Similarity threshold for typos
            
            # Check price-related queries
            price_matches = get_close_matches(query_lower, price_keywords, n=3, cutoff=threshold)
            if any(word in query_words or pm in price_keywords for pm in price_matches):
                relevant_docs.append("price_list")
                # If we found price match, don't check other categories
                return relevant_docs

            # Check store-related queries
            store_matches = get_close_matches(query_lower, store_keywords, n=5, cutoff=threshold)
            store_words = query_words.union(set(store_matches))
            if any(sw in store_keywords for sw in store_words):
                relevant_docs.append("about_us")

            # Special case: Combined price+store queries
            if not relevant_docs and ('store' in query_words and 'price' in query_words):
                return ["price_list", "about_us"]

            # Fallback for empty matches
            return relevant_docs if relevant_docs else list(self.knowledge_base.keys())

        except Exception as e:
            print(f"Document selection error: {str(e)}")
            # Fail-safe return
            return list(self.knowledge_base.keys())

    def get_response(self, messages):
        user_message = messages[-1]['content']
        
        try:
            # Block order-related responses
            order_keywords = ["order", "buy", "purchase", "add to cart", "checkout"]
            if any(kw in user_message.lower() for kw in order_keywords):
                return {
                    "role": "assistant",
                    "content": "For orders, please use our order system. Would you like to start an order now?",
                    "memory": {
                        "agent": "details_agent",
                        "action": "order_redirect"
                    }
                }

            # Existing document processing logic
            relevant_docs = self._select_relevant_documents(user_message)
            print(f"Selected documents: {relevant_docs}")

            context = []
            for doc_name in relevant_docs:
                doc_data = self.knowledge_base[doc_name]
                context.append(
                    f"===== {doc_name.upper().replace('_', ' ')} =====\n"
                    f"{doc_data['content']}\n"
                )

            prompt = f"""<<SYS>>
    You are a factual Plantify assistant. Rules:
    1. Answer ONLY using provided documents
    2. Never discuss orders/payments
    3. For missing info: "Please visit www.plantify.com for details"

    DOCUMENTS:
    {"".join(context)}
    <</SYS>>

    Question: {user_message}

    Concise answer:"""

            # Get response with proper error handling
            response = get_chatbot_response(
                client=self.client,
                model_name=self.chat_model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            ).strip()

            # Validate response quality
            invalid_phrases = [
                "i don't know", "not available", 
                "no information", "not mentioned"
            ]
            if not response or any(phrase in response.lower() for phrase in invalid_phrases):
                response = "This information isn't available in our records. Please visit www.plantify.com for details."

            return {
                "role": "assistant",
                "content": response,
                "memory": {
                    "agent": "details_agent",
                    "sources": relevant_docs,
                    "documents_used": len(relevant_docs)
                }
            }

        except Exception as e:
            print(f"DetailsAgent error: {str(e)}")
            return {
                "role": "assistant",
                "content": "I'm having trouble accessing that information. Please try again later.",
                "memory": {
                    "agent": "details_agent",
                    "error": str(e)
                }
            }
            
        
    def postprocess(self, output):
        """Maintain compatibility with existing code"""
        if isinstance(output, dict):
            return output
        return {
            "role": "assistant",
            "content": output,
            "memory": {"agent": "details_agent"}
        }