"""
MongoDB Performance Testing Suite
Author: QA Engineer
Description: Performance testing and monitoring for MongoDB operations
"""

import time
import threading
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
import json


class MongoDBPerformanceTester:
    def __init__(
        self,
        connection_string="mongodb://localhost:27017/",
        database_name="performance_test_db",
    ):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.results = []

    def cleanup(self):
        """Clean up test collections"""
        collections_to_drop = ["load_test", "stress_test", "concurrent_test"]
        for collection_name in collections_to_drop:
            if collection_name in self.db.list_collection_names():
                self.db[collection_name].drop()

    def generate_test_data(self, count=1000):
        """Generate test data for performance testing"""
        test_data = []
        for i in range(count):
            doc = {
                "user_id": random.randint(1, 10000),
                "name": f"User_{i}",
                "email": f"user{i}@example.com",
                "age": random.randint(18, 80),
                "department": random.choice(
                    ["Engineering", "Marketing", "Sales", "HR", "Finance"]
                ),
                "salary": random.randint(30000, 150000),
                "created_at": datetime.now() - timedelta(days=random.randint(0, 365)),
                "metadata": {
                    "last_login": datetime.now()
                    - timedelta(hours=random.randint(0, 720)),
                    "preferences": {
                        "theme": random.choice(["dark", "light"]),
                        "language": random.choice(["en", "id", "es", "fr"]),
                    },
                },
            }
            test_data.append(doc)
        return test_data

    def test_insert_performance(self, document_count=1000):
        """Test insert performance with different approaches"""
        collection = self.db["load_test"]

        # Clear collection first to avoid duplicate key errors
        collection.drop()

        # Generate test data
        test_data = []
        for i in range(document_count):
            doc = {
                "user_id": 1000 + i,
                "name": f"User_{i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50),
                "department": ["Engineering", "Sales", "Marketing", "HR", "Finance"][
                    i % 5
                ],
                "salary": 50000 + (i * 100),
                "created_at": datetime.now(),
                "metadata": {
                    "last_login": datetime.now() + timedelta(days=i % 30),
                    "preferences": {
                        "theme": ["light", "dark"][i % 2],
                        "language": ["en", "es", "fr"][i % 3],
                    },
                },
            }
            test_data.append(doc)

        # Test single insert
        start_time = time.time()
        for doc in test_data[:100]:  # Test with smaller subset for single inserts
            collection.insert_one(doc)
        single_insert_time = time.time() - start_time

        # Clear collection before bulk insert test
        collection.drop()

        # Test bulk insert
        start_time = time.time()
        collection.insert_many(test_data)
        bulk_insert_time = time.time() - start_time

        result = {
            "test_type": "insert_performance",
            "single_insert_time": single_insert_time,
            "bulk_insert_time": bulk_insert_time,
            "documents_count": document_count,
            "single_insert_rate": (
                100 / single_insert_time if single_insert_time > 0 else 0
            ),
            "bulk_insert_rate": (
                document_count / bulk_insert_time if bulk_insert_time > 0 else 0
            ),
        }

        self.results.append(result)
        return result

    def test_query_performance(self, iterations=100):
        """Test query operation performance"""
        collection = self.db.load_test

        # Ensure we have data
        if collection.count_documents({}) == 0:
            test_data = self.generate_test_data(10000)
            collection.insert_many(test_data)

        query_times = []

        # Test various query types
        queries = [
            {"department": "Engineering"},
            {"age": {"$gte": 30, "$lte": 50}},
            {"salary": {"$gt": 75000}},
            {"metadata.preferences.theme": "dark"},
            {"created_at": {"$gte": datetime.now() - timedelta(days=30)}},
        ]

        for query in queries:
            start_time = time.time()
            for _ in range(iterations):
                list(collection.find(query).limit(10))
            end_time = time.time()

            avg_query_time = (end_time - start_time) / iterations
            query_times.append(
                {
                    "query": str(query),
                    "avg_time": avg_query_time,
                    "queries_per_second": (
                        1 / avg_query_time if avg_query_time > 0 else 0
                    ),
                }
            )

        result = {
            "test_type": "query_performance",
            "query_results": query_times,
            "total_iterations": iterations,
        }

        self.results.append(result)
        return result

    def test_concurrent_operations(self, num_threads=10, operations_per_thread=100):
        """Test concurrent database operations"""
        collection = self.db.concurrent_test

        def worker_function(thread_id):
            thread_results = []
            for i in range(operations_per_thread):
                # Mix of operations
                operation_type = random.choice(["insert", "find", "update"])

                start_time = time.time()

                if operation_type == "insert":
                    doc = {
                        "thread_id": thread_id,
                        "operation_num": i,
                        "data": f"Thread {thread_id} - Operation {i}",
                        "timestamp": datetime.now(),
                    }
                    collection.insert_one(doc)

                elif operation_type == "find":
                    collection.find_one({"thread_id": thread_id})

                elif operation_type == "update":
                    collection.update_one(
                        {"thread_id": thread_id},
                        {"$set": {"last_updated": datetime.now()}},
                    )

                operation_time = time.time() - start_time
                thread_results.append(
                    {
                        "thread_id": thread_id,
                        "operation": operation_type,
                        "time": operation_time,
                    }
                )

            return thread_results

        # Start concurrent threads
        threads = []
        start_time = time.time()

        for i in range(num_threads):
            thread = threading.Thread(target=worker_function, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        result = {
            "test_type": "concurrent_operations",
            "num_threads": num_threads,
            "operations_per_thread": operations_per_thread,
            "total_operations": num_threads * operations_per_thread,
            "total_time": total_time,
            "operations_per_second": (num_threads * operations_per_thread) / total_time,
        }

        self.results.append(result)
        return result

    def test_aggregation_performance(self):
        """Test MongoDB aggregation pipeline performance"""
        collection = self.db.load_test

        # Ensure we have data
        if collection.count_documents({}) == 0:
            test_data = self.generate_test_data(10000)
            collection.insert_many(test_data)

        aggregation_pipelines = [
            # Group by department and calculate average salary
            [
                {
                    "$group": {
                        "_id": "$department",
                        "avg_salary": {"$avg": "$salary"},
                        "count": {"$sum": 1},
                    }
                }
            ],
            # Complex aggregation with multiple stages
            [
                {"$match": {"age": {"$gte": 25}}},
                {
                    "$group": {
                        "_id": {
                            "department": "$department",
                            "age_group": {
                                "$switch": {
                                    "branches": [
                                        {
                                            "case": {"$lt": ["$age", 30]},
                                            "then": "25-29",
                                        },
                                        {
                                            "case": {"$lt": ["$age", 40]},
                                            "then": "30-39",
                                        },
                                        {
                                            "case": {"$lt": ["$age", 50]},
                                            "then": "40-49",
                                        },
                                    ],
                                    "default": "50+",
                                }
                            },
                        },
                        "avg_salary": {"$avg": "$salary"},
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"_id.department": 1, "_id.age_group": 1}},
            ],
        ]

        aggregation_results = []
        for i, pipeline in enumerate(aggregation_pipelines):
            start_time = time.time()
            result_cursor = collection.aggregate(pipeline)
            results = list(result_cursor)
            end_time = time.time()

            aggregation_results.append(
                {
                    "pipeline_id": i + 1,
                    "execution_time": end_time - start_time,
                    "result_count": len(results),
                }
            )

        result = {
            "test_type": "aggregation_performance",
            "pipelines_tested": len(aggregation_pipelines),
            "results": aggregation_results,
        }

        self.results.append(result)
        return result

    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        report = {
            "test_summary": {
                "total_tests": len(self.results),
                "test_timestamp": datetime.now().isoformat(),
                "database": self.database_name,
            },
            "results": self.results,
        }

        # Save to JSON file
        with open(
            f"reports/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "w",
        ) as f:
            json.dump(report, f, indent=2, default=str)

        return report

    def run_full_performance_suite(self):
        """Run complete performance test suite"""
        print("Starting MongoDB Performance Test Suite...")

        # Cleanup before starting
        self.cleanup()

        # Run all performance tests
        print("1. Testing Insert Performance...")
        self.test_insert_performance(1000)

        print("2. Testing Query Performance...")
        self.test_query_performance(50)

        print("3. Testing Concurrent Operations...")
        self.test_concurrent_operations(5, 50)

        print("4. Testing Aggregation Performance...")
        self.test_aggregation_performance()

        # Generate report
        print("5. Generating Performance Report...")
        report = self.generate_performance_report()

        print("Performance testing completed!")
        return report


if __name__ == "__main__":
    # Initialize and run performance tests
    perf_tester = MongoDBPerformanceTester()
    report = perf_tester.run_full_performance_suite()

    # Print summary
    print("\n=== PERFORMANCE TEST SUMMARY ===")
    for result in report["results"]:
        print(f"Test: {result['test_type']}")
        if result["test_type"] == "insert_performance":
            print(f"  Bulk Insert Rate: {result['bulk_insert_rate']:.2f} docs/sec")
        elif result["test_type"] == "concurrent_operations":
            print(
                f"  Concurrent Ops Rate: {result['operations_per_second']:.2f} ops/sec"
            )
        print("---")
