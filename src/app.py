"""
Interactive CLI for the Agentic Search Assistant
"""
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.agent.agent import SearchAgent
from src.indexing.index_data import ProductIndexer
from config.elasticsearch import es_config


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*80)
    print("🔍 AGENTIC SEARCH ASSISTANT - Powered by Elasticsearch & Gemini")
    print("="*80)
    print("Ask natural language questions like:")
    print("  • 'laptop for programming under $1000'")
    print("  • 'affordable winter jackets for hiking'")
    print("  • 'gifts for coffee lovers'")
    print("\nType 'quit' to exit, 'reset' to clear conversation history")
    print("="*80 + "\n")


def print_results(results: list, max_results: int = 5):
    """Pretty print search results"""
    print(f"\n📦 Top {min(len(results), max_results)} Results:\n")
    
    for idx, result in enumerate(results[:max_results], 1):
        print(f"{idx}. {result['title']}")
        print(f"   💰 ${result['price']:.2f} | ⭐ {result['rating']}/5 | 🏷️ {result['category']}")
        print(f"   {result['description'][:100]}...")
        print()


def main():
    """Main CLI loop"""
    print_banner()
    
    # Test Elasticsearch connection
    print("🔌 Connecting to Elasticsearch...")
    if not es_config.test_connection():
        print("\n❌ Failed to connect to Elasticsearch!")
        print("Please ensure Elasticsearch is running:")
        print("   docker-compose up -d")
        print("\nOr configure Elastic Cloud in .env file")
        return
    
    print("\n✅ Connected to Elasticsearch!")
    
    # Initialize agent
    try:
        print("\n🤖 Initializing search agent with Gemini...")
        agent = SearchAgent()
        print("✅ Agent ready!\n")
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {e}")
        print("Please check your GEMINI_API_KEY in .env file")
        return
    
    # Main conversation loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for using Agentic Search! Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                agent.reset_conversation()
                continue
            
            if user_input.lower() == 'help':
                print_banner()
                continue
            
            # Process query
            print()  # Blank line for readability
            result = agent.chat(user_input)
            
            # Display agent response
            print(f"\n🤖 Assistant:\n{result['response']}\n")
            
            # Display search results
            if result['results']:
                print_results(result['results'])
            
        except KeyboardInterrupt:
            print("\n\n👋 Thanks for using Agentic Search! Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit\n")


if __name__ == "__main__":
    main()
