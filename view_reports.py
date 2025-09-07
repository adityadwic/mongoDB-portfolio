#!/usr/bin/env python3
"""
Quick Test Report Viewer
Author: QA Engineer
Description: Quick script to view test reports
"""

import os
import webbrowser


def main():
    reports_dir = "reports"

    if not os.path.exists(reports_dir):
        print("❌ Reports directory not found!")
        print("Please run tests first: python run_tests.py")
        return

    # Find latest HTML report
    html_files = [f for f in os.listdir(reports_dir) if f.endswith(".html")]

    if html_files:
        latest_html = sorted(html_files)[-1]
        html_path = os.path.abspath(os.path.join(reports_dir, latest_html))

        print(f"📊 Opening test report: {latest_html}")
        print(f"📁 Location: {html_path}")

        # Open in browser
        webbrowser.open(f"file://{html_path}")
        print("✅ Report opened in browser!")
    else:
        print("❌ No HTML reports found!")
        print("Generate reports first: python report_generator.py")

    # List all available reports
    print(f"\n📋 Available Reports in {reports_dir}/:")
    for file in sorted(os.listdir(reports_dir)):
        print(f"  - {file}")


if __name__ == "__main__":
    main()
