"""
MongoDB Connection and CRUD Operations Test Suite
Author: QA Engineer
Description: Comprehensive testing for MongoDB basic operations
"""

import pytest
from pymongo import MongoClient
from datetime import datetime
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBTester:
    def __init__(
        self, connection_string="mongodb://localhost:27017/", database_name="test_db"
    ):
        """Initialize MongoDB connection"""
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                self.connection_string, serverSelectionTimeoutMS=5000
            )
            # Test connection
            self.client.admin.command("ismaster")
            self.db = self.client[self.database_name]
            logger.info("Successfully connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")


class TestMongoDBConnection:
    """Test MongoDB connection functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.tester = MongoDBTester()

    def teardown_method(self):
        """Cleanup after each test"""
        self.tester.disconnect()

    def test_connection_success(self):
        """Test successful MongoDB connection"""
        assert self.tester.connect() is True
        assert self.tester.client is not None
        assert self.tester.db is not None

    def test_connection_invalid_host(self):
        """Test connection with invalid host"""
        invalid_tester = MongoDBTester("mongodb://invalid-host:27017/")
        assert invalid_tester.connect() is False

    def test_database_selection(self):
        """Test database selection"""
        self.tester.connect()
        assert self.tester.db.name == "test_db"


class TestMongoDBCRUDOperations:
    """Test MongoDB CRUD operations"""

    def setup_method(self):
        """Setup for each test"""
        self.tester = MongoDBTester()
        self.tester.connect()
        self.collection = self.tester.db.test_collection
        # Clean up collection before each test
        self.collection.delete_many({})

    def teardown_method(self):
        """Cleanup after each test"""
        # Clean up collection after each test
        self.collection.delete_many({})
        self.tester.disconnect()

    def test_create_single_document(self):
        """Test creating a single document"""
        test_doc = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "created_at": datetime.now(),
        }

        result = self.collection.insert_one(test_doc)
        assert result.inserted_id is not None

        # Verify document was inserted
        found_doc = self.collection.find_one({"_id": result.inserted_id})
        assert found_doc["name"] == "John Doe"
        assert found_doc["email"] == "john@example.com"

    def test_create_multiple_documents(self):
        """Test creating multiple documents"""
        test_docs = [
            {"name": "Alice", "department": "Engineering", "salary": 75000},
            {"name": "Bob", "department": "Marketing", "salary": 65000},
            {"name": "Charlie", "department": "Engineering", "salary": 80000},
        ]

        result = self.collection.insert_many(test_docs)
        assert len(result.inserted_ids) == 3

        # Verify all documents were inserted
        count = self.collection.count_documents({})
        assert count == 3

    def test_read_documents(self):
        """Test reading documents with various queries"""
        # Insert test data
        test_docs = [
            {"name": "Alice", "age": 25, "city": "New York"},
            {"name": "Bob", "age": 30, "city": "San Francisco"},
            {"name": "Charlie", "age": 35, "city": "New York"},
        ]
        self.collection.insert_many(test_docs)

        # Test find all
        all_docs = list(self.collection.find({}))
        assert len(all_docs) == 3

        # Test find with filter
        ny_docs = list(self.collection.find({"city": "New York"}))
        assert len(ny_docs) == 2

        # Test find one
        alice = self.collection.find_one({"name": "Alice"})
        assert alice["age"] == 25

        # Test find with projection
        names_only = list(self.collection.find({}, {"name": 1, "_id": 0}))
        assert all("name" in doc and len(doc) == 1 for doc in names_only)

    def test_update_documents(self):
        """Test updating documents"""
        # Insert test document
        test_doc = {"name": "John", "age": 25, "status": "active"}
        result = self.collection.insert_one(test_doc)
        doc_id = result.inserted_id

        # Test update one
        self.collection.update_one(
            {"_id": doc_id}, {"$set": {"age": 26, "last_updated": datetime.now()}}
        )

        updated_doc = self.collection.find_one({"_id": doc_id})
        assert updated_doc["age"] == 26
        assert "last_updated" in updated_doc

        # Test update many
        self.collection.insert_many(
            [
                {"status": "inactive", "category": "A"},
                {"status": "inactive", "category": "B"},
            ]
        )

        update_result = self.collection.update_many(
            {"status": "inactive"}, {"$set": {"status": "archived"}}
        )
        assert update_result.modified_count == 2

    def test_delete_documents(self):
        """Test deleting documents"""
        # Insert test documents
        test_docs = [
            {"name": "temp1", "temp": True},
            {"name": "temp2", "temp": True},
            {"name": "permanent", "temp": False},
        ]
        self.collection.insert_many(test_docs)

        # Test delete one
        delete_result = self.collection.delete_one({"name": "temp1"})
        assert delete_result.deleted_count == 1

        # Test delete many
        delete_result = self.collection.delete_many({"temp": True})
        assert delete_result.deleted_count == 1

        # Verify only permanent document remains
        remaining = self.collection.count_documents({})
        assert remaining == 1


class TestMongoDBIndexes:
    """Test MongoDB index operations"""

    def setup_method(self):
        """Setup for each test"""
        self.tester = MongoDBTester()
        self.tester.connect()
        self.collection = self.tester.db.index_test_collection
        self.collection.delete_many({})
        self.collection.drop_indexes()

    def teardown_method(self):
        """Cleanup after each test"""
        self.collection.drop_indexes()
        self.collection.delete_many({})
        self.tester.disconnect()

    def test_create_single_field_index(self):
        """Test creating single field index"""
        # Create index
        self.collection.create_index("email")

        # Verify index exists
        indexes = list(self.collection.list_indexes())
        index_names = [idx["name"] for idx in indexes]
        assert "email_1" in index_names

    def test_create_compound_index(self):
        """Test creating compound index"""
        # Create compound index
        self.collection.create_index([("department", 1), ("salary", -1)])

        # Verify index exists
        indexes = list(self.collection.list_indexes())
        index_names = [idx["name"] for idx in indexes]
        assert "department_1_salary_-1" in index_names

    def test_query_performance_with_index(self):
        """Test query performance with and without index"""
        # Insert test data
        test_data = [
            {"email": f"user{i}@example.com", "data": f"data_{i}"} for i in range(1000)
        ]
        self.collection.insert_many(test_data)

        # Test query without index
        start_time = time.time()
        result = self.collection.find_one({"email": "user500@example.com"})
        time_without_index = time.time() - start_time

        # Create index
        self.collection.create_index("email")

        # Test query with index
        start_time = time.time()
        result = self.collection.find_one({"email": "user500@example.com"})
        time_with_index = time.time() - start_time

        # Index should improve performance
        assert result is not None
        logger.info(f"Query time without index: {time_without_index:.4f}s")
        logger.info(f"Query time with index: {time_with_index:.4f}s")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
