"""
MongoDB Data Validation and Integrity Testing Suite
Author: QA Engineer
Description: Comprehensive data validation, schema testing, and integrity checks
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import json
import hashlib
import random
from faker import Faker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBDataValidator:
    def __init__(
        self,
        connection_string="mongodb://localhost:27017/",
        database_name="validation_test_db",
    ):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.fake = Faker()
        self.test_results = []

    def cleanup(self):
        """Clean up test collections"""
        collections_to_drop = [
            "schema_test",
            "integrity_test",
            "validation_test",
            "transaction_test",
        ]
        for collection_name in collections_to_drop:
            if collection_name in self.db.list_collection_names():
                self.db[collection_name].drop()

    def test_schema_validation(self):
        """Test MongoDB schema validation"""
        test_cases = []

        try:
            # Create collection with schema validation
            schema = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["name", "email", "age"],
                    "properties": {
                        "name": {
                            "bsonType": "string",
                            "description": "must be a string and is required",
                        },
                        "email": {
                            "bsonType": "string",
                            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                            "description": "must be a valid email format",
                        },
                        "age": {
                            "bsonType": "int",
                            "minimum": 0,
                            "maximum": 150,
                            "description": "must be an integer between 0 and 150",
                        },
                        "salary": {
                            "bsonType": "number",
                            "minimum": 0,
                            "description": "must be a positive number",
                        },
                    },
                }
            }

            # Drop collection if exists
            if "schema_test" in self.db.list_collection_names():
                self.db.schema_test.drop()

            # Create collection with validation
            self.db.create_collection("schema_test", validator=schema)
            collection = self.db.schema_test

            # Test 1: Valid document insertion
            valid_doc = {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "age": 30,
                "salary": 75000.50,
            }

            try:
                result = collection.insert_one(valid_doc)
                test_cases.append(
                    {
                        "test": "Valid Document Insertion",
                        "status": "PASS",
                        "details": f"Document inserted successfully with ID: {result.inserted_id}",
                    }
                )
            except Exception as e:
                test_cases.append(
                    {
                        "test": "Valid Document Insertion",
                        "status": "FAIL",
                        "details": f"Failed to insert valid document: {str(e)}",
                    }
                )

            # Test 2: Invalid document rejection (missing required field)
            invalid_doc_missing = {
                "name": "Jane Doe",
                "email": "jane@example.com",
                # Missing required 'age' field
            }

            try:
                collection.insert_one(invalid_doc_missing)
                test_cases.append(
                    {
                        "test": "Missing Required Field Rejection",
                        "status": "FAIL",
                        "details": "Document with missing required field was incorrectly accepted",
                    }
                )
            except Exception as e:
                test_cases.append(
                    {
                        "test": "Missing Required Field Rejection",
                        "status": "PASS",
                        "details": f"Correctly rejected document with missing field: {str(e)}",
                    }
                )

            # Test 3: Invalid email format rejection
            invalid_doc_email = {
                "name": "Bob Smith",
                "email": "invalid-email-format",
                "age": 25,
            }

            try:
                collection.insert_one(invalid_doc_email)
                test_cases.append(
                    {
                        "test": "Invalid Email Format Rejection",
                        "status": "FAIL",
                        "details": "Document with invalid email was incorrectly accepted",
                    }
                )
            except Exception as e:
                test_cases.append(
                    {
                        "test": "Invalid Email Format Rejection",
                        "status": "PASS",
                        "details": f"Correctly rejected document with invalid email: {str(e)}",
                    }
                )

            # Test 4: Age range validation
            invalid_doc_age = {
                "name": "Old Person",
                "email": "old@example.com",
                "age": 200,  # Exceeds maximum age
            }

            try:
                collection.insert_one(invalid_doc_age)
                test_cases.append(
                    {
                        "test": "Age Range Validation",
                        "status": "FAIL",
                        "details": "Document with invalid age was incorrectly accepted",
                    }
                )
            except Exception as e:
                test_cases.append(
                    {
                        "test": "Age Range Validation",
                        "status": "PASS",
                        "details": f"Correctly rejected document with invalid age: {str(e)}",
                    }
                )

        except Exception as e:
            test_cases.append(
                {
                    "test": "Schema Validation Setup",
                    "status": "FAIL",
                    "details": f"Failed to set up schema validation: {str(e)}",
                }
            )

        result = {
            "test_category": "Schema Validation Testing",
            "timestamp": datetime.now().isoformat(),
            "test_cases": test_cases,
        }

        self.test_results.append(result)
        return result

    def test_data_integrity(self):
        """Test data integrity and consistency"""
        test_cases = []

        try:
            collection = self.db.integrity_test
            collection.delete_many({})

            # Test 1: Data consistency after multiple operations
            original_doc = {
                "user_id": "user_001",
                "name": "Alice Johnson",
                "balance": 1000.00,
                "transactions": [],
                "created_at": datetime.now(),
            }

            result = collection.insert_one(original_doc)
            doc_id = result.inserted_id

            # Perform multiple updates
            updates = [
                {
                    "$inc": {"balance": -100},
                    "$push": {"transactions": {"type": "withdrawal", "amount": 100}},
                },
                {
                    "$inc": {"balance": 50},
                    "$push": {"transactions": {"type": "deposit", "amount": 50}},
                },
                {
                    "$inc": {"balance": -75},
                    "$push": {"transactions": {"type": "withdrawal", "amount": 75}},
                },
            ]

            for update in updates:
                collection.update_one({"_id": doc_id}, update)

            # Verify data consistency
            final_doc = collection.find_one({"_id": doc_id})
            expected_balance = 1000 - 100 + 50 - 75  # 875
            transaction_count = len(final_doc["transactions"])

            if final_doc["balance"] == expected_balance and transaction_count == 3:
                test_cases.append(
                    {
                        "test": "Data Consistency After Updates",
                        "status": "PASS",
                        "details": f"Balance: {final_doc['balance']}, Transactions: {transaction_count}",
                    }
                )
            else:
                test_cases.append(
                    {
                        "test": "Data Consistency After Updates",
                        "status": "FAIL",
                        "details": f"Expected balance: {expected_balance}, Got: {final_doc['balance']}",
                    }
                )

            # Test 2: Duplicate key handling
            unique_collection = self.db.unique_test
            unique_collection.delete_many({})
            unique_collection.create_index("email", unique=True)

            # Insert first document
            doc1 = {"name": "User 1", "email": "unique@example.com"}
            unique_collection.insert_one(doc1)

            # Try to insert duplicate
            doc2 = {"name": "User 2", "email": "unique@example.com"}
            try:
                unique_collection.insert_one(doc2)
                test_cases.append(
                    {
                        "test": "Unique Index Constraint",
                        "status": "FAIL",
                        "details": "Duplicate document was incorrectly accepted",
                    }
                )
            except Exception as e:
                test_cases.append(
                    {
                        "test": "Unique Index Constraint",
                        "status": "PASS",
                        "details": f"Correctly rejected duplicate: {str(e)}",
                    }
                )

            # Test 3: Data type consistency
            type_test_docs = [
                {"field": "string_value", "type": "string"},
                {"field": 123, "type": "integer"},
                {"field": 123.45, "type": "float"},
                {"field": True, "type": "boolean"},
                {"field": datetime.now(), "type": "datetime"},
            ]

            collection.insert_many(type_test_docs)

            # Verify data types
            type_check_passed = True
            for doc in collection.find({"type": {"$exists": True}}):
                expected_type = doc["type"]
                actual_value = doc["field"]

                if expected_type == "string" and not isinstance(actual_value, str):
                    type_check_passed = False
                elif expected_type == "integer" and not isinstance(actual_value, int):
                    type_check_passed = False
                elif expected_type == "float" and not isinstance(actual_value, float):
                    type_check_passed = False
                elif expected_type == "boolean" and not isinstance(actual_value, bool):
                    type_check_passed = False
                elif expected_type == "datetime" and not isinstance(
                    actual_value, datetime
                ):
                    type_check_passed = False

            if type_check_passed:
                test_cases.append(
                    {
                        "test": "Data Type Consistency",
                        "status": "PASS",
                        "details": "All data types preserved correctly",
                    }
                )
            else:
                test_cases.append(
                    {
                        "test": "Data Type Consistency",
                        "status": "FAIL",
                        "details": "Data type inconsistency detected",
                    }
                )

        except Exception as e:
            test_cases.append(
                {
                    "test": "Data Integrity Setup",
                    "status": "FAIL",
                    "details": f"Failed to set up integrity testing: {str(e)}",
                }
            )

        result = {
            "test_category": "Data Integrity Testing",
            "timestamp": datetime.now().isoformat(),
            "test_cases": test_cases,
        }

        self.test_results.append(result)
        return result

    def test_transaction_handling(self):
        """Test MongoDB transaction handling"""
        test_cases = []

        try:
            # Note: Transactions require replica set, this test will show how to test when available
            collection1 = self.db.account1
            collection2 = self.db.account2

            collection1.delete_many({})
            collection2.delete_many({})

            # Setup initial data
            collection1.insert_one({"account_id": "ACC001", "balance": 1000})
            collection2.insert_one({"account_id": "ACC002", "balance": 500})

            # Test transaction-like behavior (without actual transactions for single instance)
            # In a real scenario with replica set, you would use client.start_session()

            try:
                # Simulate transfer operation
                account1_before = collection1.find_one({"account_id": "ACC001"})
                account2_before = collection2.find_one({"account_id": "ACC002"})

                transfer_amount = 200

                # Debit from account 1
                collection1.update_one(
                    {"account_id": "ACC001"}, {"$inc": {"balance": -transfer_amount}}
                )

                # Credit to account 2
                collection2.update_one(
                    {"account_id": "ACC002"}, {"$inc": {"balance": transfer_amount}}
                )

                # Verify transfer
                account1_after = collection1.find_one({"account_id": "ACC001"})
                account2_after = collection2.find_one({"account_id": "ACC002"})

                expected_balance1 = account1_before["balance"] - transfer_amount
                expected_balance2 = account2_before["balance"] + transfer_amount

                if (
                    account1_after["balance"] == expected_balance1
                    and account2_after["balance"] == expected_balance2
                ):
                    test_cases.append(
                        {
                            "test": "Multi-Collection Operation",
                            "status": "PASS",
                            "details": f"Transfer successful: {transfer_amount} transferred",
                        }
                    )
                else:
                    test_cases.append(
                        {
                            "test": "Multi-Collection Operation",
                            "status": "FAIL",
                            "details": "Balance mismatch after transfer",
                        }
                    )

            except Exception as e:
                test_cases.append(
                    {
                        "test": "Multi-Collection Operation",
                        "status": "FAIL",
                        "details": f"Transfer operation failed: {str(e)}",
                    }
                )

            # Test rollback scenario simulation
            try:
                # Simulate failed operation that should be rolled back
                original_balance = collection1.find_one({"account_id": "ACC001"})[
                    "balance"
                ]

                # This would fail intentionally
                collection1.update_one(
                    {"account_id": "ACC001"},
                    {"$inc": {"balance": -5000}},  # This would make balance negative
                )

                # Check if balance went negative (business rule violation)
                updated_doc = collection1.find_one({"account_id": "ACC001"})
                if updated_doc["balance"] < 0:
                    # Rollback
                    collection1.update_one(
                        {"account_id": "ACC001"},
                        {"$set": {"balance": original_balance}},
                    )

                    test_cases.append(
                        {
                            "test": "Business Rule Validation & Rollback",
                            "status": "PASS",
                            "details": "Successfully detected rule violation and rolled back",
                        }
                    )
                else:
                    test_cases.append(
                        {
                            "test": "Business Rule Validation & Rollback",
                            "status": "FAIL",
                            "details": "Business rule violation not detected",
                        }
                    )

            except Exception as e:
                test_cases.append(
                    {
                        "test": "Business Rule Validation & Rollback",
                        "status": "FAIL",
                        "details": f"Rollback test failed: {str(e)}",
                    }
                )

        except Exception as e:
            test_cases.append(
                {
                    "test": "Transaction Testing Setup",
                    "status": "FAIL",
                    "details": f"Failed to set up transaction testing: {str(e)}",
                }
            )

        result = {
            "test_category": "Transaction Handling Testing",
            "timestamp": datetime.now().isoformat(),
            "test_cases": test_cases,
        }

        self.test_results.append(result)
        return result

    def generate_test_data(self, collection_name, count=1000):
        """Generate realistic test data using Faker"""
        collection = self.db[collection_name]
        collection.delete_many({})

        test_data = []
        for i in range(count):
            doc = {
                "user_id": f"USER_{i:06d}",
                "name": self.fake.name(),
                "email": self.fake.email(),
                "phone": self.fake.phone_number(),
                "address": {
                    "street": self.fake.street_address(),
                    "city": self.fake.city(),
                    "state": self.fake.state(),
                    "zip_code": self.fake.zipcode(),
                    "country": self.fake.country(),
                },
                "date_of_birth": datetime.combine(
                    self.fake.date_of_birth(minimum_age=18, maximum_age=80),
                    datetime.min.time(),
                ),
                "registration_date": datetime.combine(
                    self.fake.date_between(start_date="-2y", end_date="today"),
                    datetime.min.time(),
                ),
                "profile": {
                    "bio": self.fake.text(max_nb_chars=200),
                    "website": self.fake.url(),
                    "company": self.fake.company(),
                    "job_title": self.fake.job(),
                    "skills": [self.fake.word() for _ in range(random.randint(3, 8))],
                },
                "preferences": {
                    "theme": random.choice(["light", "dark", "auto"]),
                    "language": random.choice(["en", "es", "fr", "de", "ja"]),
                    "notifications": random.choice([True, False]),
                    "newsletter": random.choice([True, False]),
                },
                "metadata": {
                    "created_by": "test_suite",
                    "created_at": datetime.now(),
                    "checksum": hashlib.md5(f"USER_{i:06d}".encode()).hexdigest(),
                },
            }
            test_data.append(doc)

        collection.insert_many(test_data)
        return count

    def validate_data_quality(self, collection_name):
        """Validate data quality in a collection"""
        collection = self.db[collection_name]
        validation_results = []

        total_docs = collection.count_documents({})

        # Check for missing required fields
        required_fields = ["user_id", "name", "email"]
        for field in required_fields:
            missing_count = collection.count_documents({field: {"$exists": False}})
            validation_results.append(
                {
                    "check": f"Missing {field}",
                    "count": missing_count,
                    "percentage": (
                        (missing_count / total_docs) * 100 if total_docs > 0 else 0
                    ),
                }
            )

        # Check for duplicate emails
        pipeline = [
            {"$group": {"_id": "$email", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}},
        ]
        duplicate_emails = len(list(collection.aggregate(pipeline)))
        validation_results.append(
            {
                "check": "Duplicate emails",
                "count": duplicate_emails,
                "percentage": (
                    (duplicate_emails / total_docs) * 100 if total_docs > 0 else 0
                ),
            }
        )

        # Check for invalid email formats
        invalid_email_pattern = {
            "email": {
                "$not": {"$regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
            }
        }
        invalid_emails = collection.count_documents(invalid_email_pattern)
        validation_results.append(
            {
                "check": "Invalid email format",
                "count": invalid_emails,
                "percentage": (
                    (invalid_emails / total_docs) * 100 if total_docs > 0 else 0
                ),
            }
        )

        return {
            "collection": collection_name,
            "total_documents": total_docs,
            "validation_results": validation_results,
        }

    def generate_validation_report(self):
        """Generate comprehensive validation test report"""
        report = {
            "validation_test_summary": {
                "total_categories": len(self.test_results),
                "test_timestamp": datetime.now().isoformat(),
                "database": self.database_name,
            },
            "test_results": self.test_results,
            "recommendations": [
                "Implement comprehensive schema validation for all collections",
                "Use unique indexes to prevent duplicate data",
                "Implement data quality checks in application layer",
                "Regular data integrity audits",
                "Use transactions for multi-document operations when using replica sets",
                "Implement proper error handling and rollback mechanisms",
                "Use data validation libraries in application code",
                "Monitor data quality metrics continuously",
            ],
        }

        # Save report
        import os

        os.makedirs("reports", exist_ok=True)
        report_filename = (
            f"reports/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return report

    def run_full_validation_suite(self):
        """Run complete validation test suite"""
        print("Starting MongoDB Data Validation Test Suite...")

        # Cleanup before starting
        self.cleanup()

        print("1. Testing Schema Validation...")
        self.test_schema_validation()

        print("2. Testing Data Integrity...")
        self.test_data_integrity()

        print("3. Testing Transaction Handling...")
        self.test_transaction_handling()

        print("4. Generating Test Data...")
        self.generate_test_data("validation_test", 1000)

        print("5. Validating Data Quality...")
        quality_results = self.validate_data_quality("validation_test")

        print("6. Generating Validation Report...")
        report = self.generate_validation_report()

        print("Data validation testing completed!")
        return report, quality_results


if __name__ == "__main__":
    # Initialize and run validation tests
    validator = MongoDBDataValidator()
    report, quality_results = validator.run_full_validation_suite()

    # Print summary
    print("\n=== DATA VALIDATION TEST SUMMARY ===")
    for category in report["test_results"]:
        print(f"\n{category['test_category']}:")
        for test_case in category["test_cases"]:
            print(f"  ✓ {test_case['test']}: {test_case['status']}")

    print("\n=== DATA QUALITY RESULTS ===")
    print(f"Total documents: {quality_results['total_documents']}")
    for result in quality_results["validation_results"]:
        print(f"  {result['check']}: {result['count']} ({result['percentage']:.2f}%)")

    print("\nFull report saved to: reports/validation_report_*.json")
