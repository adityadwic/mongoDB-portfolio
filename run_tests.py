#!/usr/bin/env python3
"""
MongoDB QA Test Suite Runner
Author: QA Engineer
Description: Main test runner that executes all MongoDB QA test suites
"""

import os
import sys
import argparse
import json
from datetime import datetime
import subprocess

# Add the automation-scripts directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "automation-scripts"))


def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "return_code": -1}


def setup_environment():
    """Setup test environment"""
    print("Setting up test environment...")

    # Create reports directory
    os.makedirs("reports", exist_ok=True)
    os.makedirs("data/test-db", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Check if MongoDB is running
    mongo_check = run_command("mongosh --eval 'db.runCommand({ping: 1})' --quiet")
    if not mongo_check["success"]:
        print(
            "⚠️  Warning: MongoDB may not be running. Please ensure MongoDB is started."
        )
        return False

    print("✅ MongoDB connection verified")
    return True


def run_functional_tests():
    """Run functional test suite"""
    print("\n🧪 Running Functional Tests...")

    # Run CRUD tests
    result = run_command("python automation-scripts/mongodb_crud_tests.py")
    if result["success"]:
        print("✅ CRUD tests completed successfully")
    else:
        print("❌ CRUD tests failed")
        print(result["stderr"])

    return result["success"]


def run_performance_tests():
    """Run performance test suite"""
    print("\n⚡ Running Performance Tests...")

    result = run_command("python automation-scripts/mongodb_performance_tests.py")
    if result["success"]:
        print("✅ Performance tests completed successfully")
    else:
        print("❌ Performance tests failed")
        print(result["stderr"])

    return result["success"]


def run_security_tests():
    """Run security test suite"""
    print("\n🔒 Running Security Tests...")

    result = run_command("python automation-scripts/mongodb_security_tests.py")
    if result["success"]:
        print("✅ Security tests completed successfully")
    else:
        print("❌ Security tests failed")
        print(result["stderr"])

    return result["success"]


def run_data_validation_tests():
    """Run data validation test suite"""
    print("\n📊 Running Data Validation Tests...")

    result = run_command("python automation-scripts/mongodb_data_validation.py")
    if result["success"]:
        print("✅ Data validation tests completed successfully")
    else:
        print("❌ Data validation tests failed")
        print(result["stderr"])

    return result["success"]


def load_test_data():
    """Load sample test data into MongoDB"""
    print("\n📥 Loading test data...")

    try:
        # Load sample data using mongoimport
        data_file = "test-data/sample-datasets.json"
        if os.path.exists(data_file):
            # For demonstration, we'll just confirm the file exists
            print("✅ Test data file found")
            return True
        else:
            print("⚠️  Test data file not found")
            return False
    except Exception as e:
        print(f"❌ Failed to load test data: {e}")
        return False


def generate_summary_report(results):
    """Generate comprehensive test summary report"""
    print("\n📋 Generating Summary Report...")

    timestamp = datetime.now()

    report = {
        "test_execution_summary": {
            "timestamp": timestamp.isoformat(),
            "total_suites": len(results),
            "passed_suites": sum(1 for r in results.values() if r),
            "failed_suites": sum(1 for r in results.values() if not r),
            "overall_status": "PASS" if all(results.values()) else "FAIL",
        },
        "suite_results": {
            "functional_tests": "PASS" if results.get("functional", False) else "FAIL",
            "performance_tests": (
                "PASS" if results.get("performance", False) else "FAIL"
            ),
            "security_tests": "PASS" if results.get("security", False) else "FAIL",
            "data_validation_tests": (
                "PASS" if results.get("validation", False) else "FAIL"
            ),
        },
        "recommendations": [
            "Review failed test cases and address issues",
            "Monitor performance metrics trends",
            "Implement security recommendations",
            "Maintain data quality standards",
            "Update test cases as system evolves",
        ],
    }

    # Save summary report
    report_filename = f"reports/test_summary_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, "w") as f:
        json.dump(report, f, indent=2)

    print(f"✅ Summary report saved to: {report_filename}")

    # Print summary to console
    print("\n" + "=" * 60)
    print("📊 TEST EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Test Suites: {report['test_execution_summary']['total_suites']}")
    print(f"Passed: {report['test_execution_summary']['passed_suites']}")
    print(f"Failed: {report['test_execution_summary']['failed_suites']}")
    print(f"Overall Status: {report['test_execution_summary']['overall_status']}")
    print("\nSuite Results:")
    for suite, status in report["suite_results"].items():
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {suite.replace('_', ' ').title()}: {status}")
    print("=" * 60)

    return report


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="MongoDB QA Test Suite Runner")
    parser.add_argument(
        "--suite",
        choices=["all", "functional", "performance", "security", "validation"],
        default="all",
        help="Test suite to run",
    )
    parser.add_argument(
        "--skip-setup", action="store_true", help="Skip environment setup"
    )
    parser.add_argument(
        "--load-data", action="store_true", help="Load test data before running tests"
    )

    args = parser.parse_args()

    print("🚀 MongoDB QA Test Suite Runner")
    print("=" * 50)

    # Setup environment
    if not args.skip_setup:
        if not setup_environment():
            print("❌ Environment setup failed. Exiting.")
            sys.exit(1)

    # Load test data if requested
    if args.load_data:
        load_test_data()

    # Track test results
    results = {}

    # Run selected test suites
    if args.suite in ["all", "functional"]:
        results["functional"] = run_functional_tests()

    if args.suite in ["all", "performance"]:
        results["performance"] = run_performance_tests()

    if args.suite in ["all", "security"]:
        results["security"] = run_security_tests()

    if args.suite in ["all", "validation"]:
        results["validation"] = run_data_validation_tests()

    # Generate summary report
    summary_report = generate_summary_report(results)

    # Exit with appropriate code
    if summary_report["test_execution_summary"]["overall_status"] == "PASS":
        print("\n🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the reports.")
        sys.exit(1)


if __name__ == "__main__":
    main()
