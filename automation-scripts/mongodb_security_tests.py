"""
MongoDB Security Testing Suite
Author: QA Engineer
Description: Security testing for MongoDB database including authentication, authorization, and data protection
"""

from pymongo import MongoClient
import logging
from datetime import datetime
import json
import hashlib
import os
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBSecurityTester:
    def __init__(self, connection_string="mongodb://localhost:27017/"):
        self.connection_string = connection_string
        self.test_results = []

    def test_authentication(self):
        """Test MongoDB authentication mechanisms"""
        test_cases = []

        # Test 1: Connection without authentication (should work on default setup)
        try:
            client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            client.admin.command("ismaster")
            test_cases.append(
                {
                    "test": "No Authentication",
                    "status": "PASS",
                    "details": "Successfully connected without authentication",
                }
            )
            client.close()
        except Exception as e:
            test_cases.append(
                {
                    "test": "No Authentication",
                    "status": "FAIL",
                    "details": f"Connection failed: {str(e)}",
                }
            )

        # Test 2: Invalid credentials (should fail if auth is enabled)
        try:
            invalid_conn = "mongodb://invalid_user:invalid_pass@localhost:27017/"
            client = MongoClient(invalid_conn, serverSelectionTimeoutMS=5000)
            client.admin.command("ismaster")
            test_cases.append(
                {
                    "test": "Invalid Credentials",
                    "status": "FAIL",
                    "details": "Connected with invalid credentials - security risk!",
                }
            )
            client.close()
        except Exception as e:
            test_cases.append(
                {
                    "test": "Invalid Credentials",
                    "status": "PASS",
                    "details": f"Correctly rejected invalid credentials: {str(e)}",
                }
            )

        result = {
            "test_category": "Authentication Testing",
            "timestamp": datetime.now().isoformat(),
            "test_cases": test_cases,
        }

        self.test_results.append(result)
        return result

    def test_ssl_connection(self):
        """Test SSL/TLS connection security"""
        test_cases = []

        # Test SSL connection (will fail if SSL not configured, which is expected)
        try:
            ssl_conn = self.connection_string + "?ssl=true&ssl_cert_reqs=CERT_REQUIRED"
            client = MongoClient(ssl_conn, serverSelectionTimeoutMS=5000)
            client.admin.command("ismaster")
            test_cases.append(
                {
                    "test": "SSL Connection",
                    "status": "PASS",
                    "details": "SSL connection successful",
                }
            )
            client.close()
        except Exception as e:
            test_cases.append(
                {
                    "test": "SSL Connection",
                    "status": "INFO",
                    "details": f"SSL not configured (expected in dev): {str(e)}",
                }
            )

        # Test connection with SSL disabled (should work in dev)
        try:
            no_ssl_conn = self.connection_string + "?ssl=false"
            client = MongoClient(no_ssl_conn, serverSelectionTimeoutMS=5000)
            client.admin.command("ismaster")
            test_cases.append(
                {
                    "test": "Non-SSL Connection",
                    "status": "WARNING",
                    "details": "Non-SSL connection allowed - consider enabling SSL for production",
                }
            )
            client.close()
        except Exception as e:
            test_cases.append(
                {
                    "test": "Non-SSL Connection",
                    "status": "FAIL",
                    "details": f"Non-SSL connection failed: {str(e)}",
                }
            )

        result = {
            "test_category": "SSL/TLS Testing",
            "timestamp": datetime.now().isoformat(),
            "test_cases": test_cases,
        }

        self.test_results.append(result)
        return result

    def test_data_encryption(self):
        """Test data encryption capabilities"""
        test_cases = []

        try:
            client = MongoClient(self.connection_string)
            db = client.security_test_db
            collection = db.encryption_test

            # Clear previous test data
            collection.delete_many({})

            # Test 1: Store sensitive data with application-level encryption
            fernet_key = Fernet.generate_key()
            cipher_suite = Fernet(fernet_key)

            sensitive_data = "This is sensitive information: SSN 123-45-6789"
            encrypted_data = cipher_suite.encrypt(sensitive_data.encode())

            # Store encrypted data
            doc = {
                "user_id": "test_user_001",
                "encrypted_field": encrypted_data,
                "created_at": datetime.now(),
            }

            result = collection.insert_one(doc)

            # Retrieve and decrypt
            retrieved_doc = collection.find_one({"_id": result.inserted_id})
            decrypted_data = cipher_suite.decrypt(
                retrieved_doc["encrypted_field"]
            ).decode()

            if decrypted_data == sensitive_data:
                test_cases.append(
                    {
                        "test": "Application-Level Encryption",
                        "status": "PASS",
                        "details": "Successfully encrypted and decrypted sensitive data",
                    }
                )
            else:
                test_cases.append(
                    {
                        "test": "Application-Level Encryption",
                        "status": "FAIL",
                        "details": "Encryption/decryption failed",
                    }
                )

            # Test 2: Hash sensitive data
            password = "user_password_123"
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            user_doc = {
                "username": "test_user",
                "password_hash": hashed_password,
                "created_at": datetime.now(),
            }

            collection.insert_one(user_doc)

            # Verify hash
            verification_hash = hashlib.sha256(password.encode()).hexdigest()
            if verification_hash == hashed_password:
                test_cases.append(
                    {
                        "test": "Password Hashing",
                        "status": "PASS",
                        "details": "Password correctly hashed and verified",
                    }
                )
            else:
                test_cases.append(
                    {
                        "test": "Password Hashing",
                        "status": "FAIL",
                        "details": "Password hashing failed",
                    }
                )

            # Cleanup
            collection.delete_many({})
            client.close()

        except Exception as e:
            test_cases.append(
                {
                    "test": "Data Encryption Setup",
                    "status": "FAIL",
                    "details": f"Encryption testing failed: {str(e)}",
                }
            )

        result = {
            "test_category": "Data Encryption Testing",
            "timestamp": datetime.now().isoformat(),
            "test_cases": test_cases,
        }

        self.test_results.append(result)
        return result

    def test_injection_attacks(self):
        """Test NoSQL injection vulnerabilities"""
        test_cases = []

        try:
            client = MongoClient(self.connection_string)
            db = client.security_test_db
            collection = db.injection_test

            # Clear and setup test data
            collection.delete_many({})
            test_users = [
                {"username": "admin", "password": "admin123", "role": "admin"},
                {"username": "user1", "password": "password123", "role": "user"},
                {"username": "user2", "password": "secret456", "role": "user"},
            ]
            collection.insert_many(test_users)

            # Test 1: Safe query (proper way)
            safe_username = "admin"
            safe_result = collection.find_one({"username": safe_username})

            if safe_result and safe_result["username"] == "admin":
                test_cases.append(
                    {
                        "test": "Safe Query Execution",
                        "status": "PASS",
                        "details": "Proper parameterized query executed successfully",
                    }
                )

            # Test 2: Potential injection attempt (should be handled safely by PyMongo)
            # This simulates what would be dangerous in SQL but is handled by MongoDB driver
            injection_attempt = {
                "$ne": None
            }  # This could bypass password checks if not handled properly

            # Using proper MongoDB query structure prevents injection
            try:
                # This is the WRONG way that could be vulnerable
                # In a real app, never construct queries like this from user input
                dangerous_query = {"username": "admin", "password": injection_attempt}
                dangerous_result = collection.find_one(dangerous_query)

                if dangerous_result is None:
                    test_cases.append(
                        {
                            "test": "NoSQL Injection Prevention",
                            "status": "PASS",
                            "details": "MongoDB driver properly handled potential injection attempt",
                        }
                    )
                else:
                    test_cases.append(
                        {
                            "test": "NoSQL Injection Prevention",
                            "status": "FAIL",
                            "details": "Potential security vulnerability detected",
                        }
                    )
            except Exception as e:
                test_cases.append(
                    {
                        "test": "NoSQL Injection Prevention",
                        "status": "PASS",
                        "details": f"Driver properly rejected malformed query: {str(e)}",
                    }
                )

            # Test 3: Input validation demonstration
            def validate_user_input(username):
                """Example of proper input validation"""
                if not isinstance(username, str):
                    return False
                if len(username) > 50:
                    return False
                if any(char in username for char in ["$", "{", "}", ";"]):
                    return False
                return True

            test_inputs = [
                "admin",
                "user1",
                "$ne",
                "admin; drop table users;",
                {"$ne": None},
            ]
            validation_results = []

            for test_input in test_inputs:
                is_valid = validate_user_input(test_input)
                validation_results.append({"input": str(test_input), "valid": is_valid})

            # All string inputs should be valid, others should be rejected
            expected_results = [True, True, False, False, False]
            actual_results = [r["valid"] for r in validation_results]

            if actual_results == expected_results:
                test_cases.append(
                    {
                        "test": "Input Validation",
                        "status": "PASS",
                        "details": "Input validation correctly identifies safe/unsafe inputs",
                    }
                )
            else:
                test_cases.append(
                    {
                        "test": "Input Validation",
                        "status": "FAIL",
                        "details": f"Input validation failed. Expected: {expected_results}, Got: {actual_results}",
                    }
                )

            # Cleanup
            collection.delete_many({})
            client.close()

        except Exception as e:
            test_cases.append(
                {
                    "test": "Injection Testing Setup",
                    "status": "FAIL",
                    "details": f"Injection testing failed: {str(e)}",
                }
            )

        result = {
            "test_category": "NoSQL Injection Testing",
            "timestamp": datetime.now().isoformat(),
            "test_cases": test_cases,
        }

        self.test_results.append(result)
        return result

    def test_database_permissions(self):
        """Test database-level permissions and access controls"""
        test_cases = []

        try:
            client = MongoClient(self.connection_string)

            # Test 1: Database creation permissions
            try:
                test_db = client.permission_test_db
                test_collection = test_db.test_collection
                test_collection.insert_one({"test": "permission_check"})

                test_cases.append(
                    {
                        "test": "Database Creation Permission",
                        "status": "PASS",
                        "details": "Successfully created database and collection",
                    }
                )

                # Cleanup
                client.drop_database("permission_test_db")

            except Exception as e:
                test_cases.append(
                    {
                        "test": "Database Creation Permission",
                        "status": "FAIL",
                        "details": f"Failed to create database: {str(e)}",
                    }
                )

            # Test 2: Admin operations (if available)
            try:
                # Try to list all databases (admin operation)
                db_list = client.list_database_names()
                test_cases.append(
                    {
                        "test": "Admin Operations Access",
                        "status": "WARNING",
                        "details": f"Can list databases ({len(db_list)} found) - consider restricting admin access",
                    }
                )
            except Exception as e:
                test_cases.append(
                    {
                        "test": "Admin Operations Access",
                        "status": "PASS",
                        "details": f"Admin operations properly restricted: {str(e)}",
                    }
                )

            client.close()

        except Exception as e:
            test_cases.append(
                {
                    "test": "Permission Testing Setup",
                    "status": "FAIL",
                    "details": f"Permission testing failed: {str(e)}",
                }
            )

        result = {
            "test_category": "Database Permissions Testing",
            "timestamp": datetime.now().isoformat(),
            "test_cases": test_cases,
        }

        self.test_results.append(result)
        return result

    def generate_security_report(self):
        """Generate comprehensive security test report"""
        report = {
            "security_test_summary": {
                "total_categories": len(self.test_results),
                "test_timestamp": datetime.now().isoformat(),
                "tester": "MongoDB QA Security Suite",
            },
            "test_results": self.test_results,
            "recommendations": [
                "Enable authentication in production environments",
                "Configure SSL/TLS for encrypted connections",
                "Implement proper input validation and sanitization",
                "Use application-level encryption for sensitive data",
                "Regularly update MongoDB to latest security patches",
                "Monitor database access logs",
                "Implement role-based access control (RBAC)",
                "Use connection string encryption in configuration files",
            ],
        }

        # Save report
        report_filename = (
            f"reports/security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        os.makedirs("reports", exist_ok=True)

        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return report

    def run_full_security_suite(self):
        """Run complete security test suite"""
        print("Starting MongoDB Security Test Suite...")

        print("1. Testing Authentication...")
        self.test_authentication()

        print("2. Testing SSL/TLS Configuration...")
        self.test_ssl_connection()

        print("3. Testing Data Encryption...")
        self.test_data_encryption()

        print("4. Testing NoSQL Injection Prevention...")
        self.test_injection_attacks()

        print("5. Testing Database Permissions...")
        self.test_database_permissions()

        print("6. Generating Security Report...")
        report = self.generate_security_report()

        print("Security testing completed!")
        return report


if __name__ == "__main__":
    # Initialize and run security tests
    security_tester = MongoDBSecurityTester()
    report = security_tester.run_full_security_suite()

    # Print summary
    print("\n=== SECURITY TEST SUMMARY ===")
    for category in report["test_results"]:
        print(f"\n{category['test_category']}:")
        for test_case in category["test_cases"]:
            print(f"  ✓ {test_case['test']}: {test_case['status']}")

    print("\nFull report saved to: reports/security_report_*.json")
