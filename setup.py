"""
Setup script to index sample products into Elasticsearch
"""
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.indexing.index_data import ProductIndexer
from config.elasticsearch import es_config


def load_products(file_path: str):
    """Load products from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    print("="*80)
    print("🚀 ELASTICSEARCH VECTOR SEARCH SETUP")
    print("="*80)
    
    # Test Elasticsearch connection
    print("\n1️⃣ Testing Elasticsearch connection...")
    if not es_config.test_connection():
        print("\n❌ Failed to connect to Elasticsearch!")
        print("\nPlease ensure Elasticsearch is running:")
        print("   docker-compose up -d")
        print("\nOr configure Elastic Cloud connection in .env file:")
        print("   ELASTICSEARCH_CLOUD_ID=your_cloud_id")
        print("   ELASTICSEARCH_API_KEY=your_api_key")
        return
    
    print("✅ Connection successful!")
    
    # Load products
    print("\n2️⃣ Loading product data...")
    data_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'data',
        'products.json'
    )
    
    try:
        products = load_products(data_file)
        print(f"✅ Loaded {len(products)} products")
    except Exception as e:
        print(f"❌ Failed to load products: {e}")
        return
    
    # Create indexer
    print("\n3️⃣ Creating Elasticsearch index with vector capabilities...")
    indexer = ProductIndexer()
    
    try:
        indexer.create_index()
        print("✅ Index created successfully!")
    except Exception as e:
        print(f"❌ Failed to create index: {e}")
        return
    
    # Index products
    print("\n4️⃣ Generating embeddings and indexing products...")
    print("   (This may take a minute for embedding generation...)")
    
    try:
        indexer.index_products(products)
        print("\n✅ All products indexed successfully!")
    except Exception as e:
        print(f"\n❌ Failed to index products: {e}")
        return
    
    # Summary
    print("\n" + "="*80)
    print("✨ SETUP COMPLETE!")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   • Index name: {indexer.index_name}")
    print(f"   • Products indexed: {len(products)}")
    print(f"   • Vector dimensions: {indexer.client.indices.get_mapping(index=indexer.index_name)[indexer.index_name]['mappings']['properties']['combined_vector']['dims']}")
    print(f"\n🎉 You can now run the agent:")
    print(f"   python src/app.py")
    print(f"\n   Or test search directly:")
    print(f"   python src/search/hybrid_search.py")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
