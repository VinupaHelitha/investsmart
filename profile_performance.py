"""
Performance Profiling Script for InvestSmart 4.0
Identifies bottlenecks and measures baseline performance
"""

import os
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def measure_api_latency():
    """Measure latency of key API calls"""
    logger.info("\n" + "="*60)
    logger.info("MEASURING API LATENCIES")
    logger.info("="*60)

    results = []

    try:
        import requests

        # Test endpoints that app.py uses
        api_tests = [
            ("Yahoo Finance (S&P 500)", "https://query1.finance.yahoo.com/v8/finance/chart/^GSPC"),
            ("FRED API (sample)", "https://api.stlouisfed.org/fred/series/UNRATE"),
            ("World Bank API (sample)", "https://api.worldbank.org/v2/country/US/indicator/NY.GDP.MKTP.CD"),
        ]

        for test_name, url in api_tests:
            logger.info(f"Testing: {test_name}")
            times = []

            for attempt in range(3):
                try:
                    start = time.time()
                    response = requests.get(url, timeout=10)
                    elapsed = time.time() - start
                    times.append(elapsed)
                    logger.info(f"  Attempt {attempt+1}: {elapsed:.2f}s (Status: {response.status_code})")
                except Exception as e:
                    logger.warning(f"  Attempt {attempt+1} failed: {type(e).__name__}")

            if times:
                avg_time = sum(times) / len(times)
                results.append({
                    'api': test_name,
                    'avg_latency': avg_time,
                    'attempts': len(times),
                    'status': 'success' if avg_time < 5 else 'slow'
                })
            else:
                results.append({
                    'api': test_name,
                    'avg_latency': 0,
                    'attempts': 0,
                    'status': 'offline'
                })

    except Exception as e:
        logger.error(f"API testing failed: {str(e)}")

    return results

def analyze_app_code():
    """Analyze app.py for common performance issues"""
    logger.info("\n" + "="*60)
    logger.info("ANALYZING APP.PY FOR PERFORMANCE ISSUES")
    logger.info("="*60)

    app_path = "app.py"
    issues = []

    try:
        with open(app_path, 'r') as f:
            content = f.read()

        checks = {
            'st.cache_data': ('Cache decorators found', content.count('@st.cache_data')),
            'for loop': ('For loops (potential vectorization)', content.count('for ')),
            'requests.get': ('Direct API calls (check batching)', content.count('requests.get')),
            'st.write': ('st.write calls (widgets)', content.count('st.write')),
            'st.dataframe': ('Dataframe renders', content.count('st.dataframe')),
            'st.metric': ('Metric displays', content.count('st.metric')),
            'plotly': ('Plotly charts', content.count('plotly')),
        }

        for check_name, (description, count) in checks.items():
            if count > 0:
                logger.info(f"  {description}: {count}")
                issues.append({
                    'type': check_name,
                    'description': description,
                    'count': count
                })

    except Exception as e:
        logger.error(f"Could not analyze app.py: {str(e)}")

    return issues

def generate_report(api_results, code_issues):
    """Generate performance baseline report"""
    logger.info("\n" + "="*60)
    logger.info("GENERATING PERFORMANCE REPORT")
    logger.info("="*60)

    # Build report
    report = f"# InvestSmart 4.0 - Performance Baseline Report\n"
    report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    report += "## API Latency Measurements\n\n"
    report += "| API | Avg Latency | Status |\n"
    report += "|-----|-------------|--------|\n"

    for result in api_results:
        status_emoji = "⚠️" if result['status'] == 'slow' else ("❌" if result['status'] == 'offline' else "✅")
        latency_str = f"{result['avg_latency']:.2f}s" if result['avg_latency'] > 0 else "N/A"
        report += f"| {result['api']} | {latency_str} | {status_emoji} {result['status']} |\n"

    report += "\n## Code Analysis\n\n"
    report += "### Performance-Related Patterns Found\n"
    report += "| Pattern | Count | Notes |\n"
    report += "|---------|-------|-------|\n"

    for issue in code_issues:
        report += f"| {issue['description']} | {issue['count']} | Check for optimization opportunities |\n"

    # Extract counts safely
    cache_count = next((i['count'] for i in code_issues if i['type'] == 'st.cache_data'), 0)
    loop_count = next((i['count'] for i in code_issues if i['type'] == 'for loop'), 0)
    api_count = next((i['count'] for i in code_issues if i['type'] == 'requests.get'), 0)
    metric_count = next((i['count'] for i in code_issues if i['type'] == 'st.metric'), 0)
    write_count = next((i['count'] for i in code_issues if i['type'] == 'st.write'), 0)
    dataframe_count = next((i['count'] for i in code_issues if i['type'] == 'st.dataframe'), 0)
    plotly_count = next((i['count'] for i in code_issues if i['type'] == 'plotly'), 0)

    report += "\n## Code Optimization Opportunities\n\n"
    report += f"- **Cache Decorators:** {cache_count} found (good coverage)\n"
    report += f"- **For Loops:** {loop_count} found (review for vectorization)\n"
    report += f"- **Direct API Calls:** {api_count} found (check for batching)\n"
    report += f"- **Widgets:** {metric_count} st.metric + {write_count} st.write + {dataframe_count} st.dataframe\n"
    report += f"- **Plotly Charts:** {plotly_count} found\n"

    report += "\n## Recommendations\n\n"
    report += "### High Priority\n"
    report += "1. Review all `requests.get()` calls for batching opportunities\n"
    report += "2. Optimize `for` loops - consider NumPy/Pandas vectorization\n"
    report += "3. Verify cache durations are appropriate for each data type\n"

    report += "\n### Medium Priority\n"
    report += "1. Check if all expensive operations are cached\n"
    report += "2. Consider lazy-loading for non-critical UI elements\n"
    report += "3. Monitor widget render times\n"

    report += "\n### Low Priority\n"
    report += "1. Consider pagination for large datasets\n"
    report += "2. Add progress indicators for long operations\n"
    report += "3. Monitor memory usage patterns\n"

    report += "\n## Next Steps\n\n"
    report += "1. Identify specific functions causing slowness\n"
    report += "2. Measure dashboard load time under realistic conditions\n"
    report += "3. Measure portfolio calculation time with large datasets\n"
    report += "4. Profile memory usage\n"
    report += "5. Create targeted optimization plan\n"

    report += "\n---\n"
    report += "**Status:** Baseline established - ready for optimization work\n"

    return report

def main():
    """Run complete performance profiling"""
    logger.info("="*60)
    logger.info("InvestSmart 4.0 - PERFORMANCE PROFILING")
    logger.info("="*60)

    api_results = measure_api_latency()
    code_issues = analyze_app_code()
    report = generate_report(api_results, code_issues)

    report_path = "PHASE_6_PERFORMANCE_BASELINE.md"
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"\n✓ Report saved to: {report_path}")
    logger.info("\n" + "="*60)
    logger.info("PROFILING COMPLETE")
    logger.info("="*60)

    return report

if __name__ == "__main__":
    main()
