"""
Intelligent search agent using LLM for query understanding and response generation
"""
import os
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.search.hybrid_search import HybridSearch
from src.agent.prompts import (
    QUERY_UNDERSTANDING_PROMPT,
    RESPONSE_GENERATION_PROMPT,
    CONVERSATION_CONTEXT_PROMPT
)

load_dotenv()


class SearchAgent:
    """
    Intelligent search agent that:
    1. Understands natural language queries using LLM
    2. Extracts filters and search intent
    3. Performs hybrid search
    4. Generates helpful, conversational responses
    """
    
    def __init__(self):
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            os.getenv("AGENT_MODEL", "gemini-1.5-flash")
        )
        
        # Initialize search engine
        self.searcher = HybridSearch()
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = int(os.getenv("MAX_CONVERSATION_HISTORY", 5))
    
    def chat(self, user_query: str) -> Dict[str, Any]:
        """
        Main chat interface for the agent
        
        Args:
            user_query: User's natural language query
            
        Returns:
            Dictionary with agent response and search results
        """
        print(f"\n🤖 Processing query: {user_query}")
        
        # Step 1: Understand the query using LLM
        query_analysis = self._understand_query(user_query)
        print(f"   Intent: {query_analysis['intent']}")
        print(f"   Search terms: {query_analysis['search_terms']}")
        
        if query_analysis['filters']:
            print(f"   Filters: {query_analysis['filters']}")
        
        # Step 2: Perform hybrid search
        search_results = self.searcher.search(
            query=query_analysis['search_terms'],
            top_k=10,
            filters=query_analysis['filters']
        )
        print(f"   Found {len(search_results)} results")
        
        # Step 3: Generate conversational response
        agent_response = self._generate_response(
            user_query=user_query,
            intent=query_analysis['intent'],
            results=search_results
        )
        
        # Update conversation history
        self._update_history(user_query, agent_response)
        
        return {
            'query': user_query,
            'intent': query_analysis['intent'],
            'filters': query_analysis['filters'],
            'results': search_results,
            'response': agent_response,
            'result_count': len(search_results)
        }
    
    def _understand_query(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to understand query and extract structured information
        """
        prompt = QUERY_UNDERSTANDING_PROMPT.format(query=query)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            
            analysis = json.loads(response.text)
            
            # Clean up filters (remove nulls)
            if 'filters' in analysis:
                analysis['filters'] = {
                    k: v for k, v in analysis['filters'].items() 
                    if v is not None
                }
            
            return analysis
        
        except Exception as e:
            print(f"   ⚠️ Query understanding failed, using fallback: {e}")
            # Fallback to basic search
            return {
                'search_terms': query,
                'filters': {},
                'intent': query
            }
    
    def _generate_response(
        self,
        user_query: str,
        intent: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate helpful conversational response using LLM
        """
        if not results:
            return "I couldn't find any products matching your criteria. Could you try adjusting your requirements or search for something else?"
        
        # Format results for LLM
        results_text = ""
        for idx, result in enumerate(results[:5], 1):  # Top 5 results
            results_text += f"\n{idx}. {result['title']}\n"
            results_text += f"   Price: ${result['price']}\n"
            results_text += f"   Rating: {result['rating']}/5\n"
            results_text += f"   Description: {result['description'][:150]}...\n"
        
        prompt = RESPONSE_GENERATION_PROMPT.format(
            query=user_query,
            intent=intent,
            results=results_text
        )
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(temperature=0.7)
            )
            return response.text
        
        except Exception as e:
            print(f"   ⚠️ Response generation failed: {e}")
            # Fallback response
            return f"I found {len(results)} products that match '{user_query}'. The top result is {results[0]['title']} for ${results[0]['price']}."
    
    def _update_history(self, user_query: str, agent_response: str):
        """Update conversation history"""
        self.conversation_history.append({
            'user': user_query,
            'agent': agent_response
        })
        
        # Keep only recent history
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("🔄 Conversation reset")


if __name__ == "__main__":
    # Test the agent
    agent = SearchAgent()
    
    test_queries = [
        "I need a laptop for programming under $1000",
        "What are some good gifts for coffee lovers?",
        "Show me affordable winter jackets for hiking"
    ]
    
    for query in test_queries:
        print("\n" + "="*80)
        result = agent.chat(query)
        print(f"\n💬 Agent Response:\n{result['response']}")
        print(f"\n📊 Found {result['result_count']} results")
