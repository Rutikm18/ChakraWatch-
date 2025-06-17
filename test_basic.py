# test_basic.py - Basic functionality tests
import requests
import json
import time
import sys
from datetime import datetime

# Test configuration
API_BASE = "http://localhost:8000"
TIMEOUT = 30

def print_header(title):
    """Print test section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def print_result(test_name, success, message=""):
    """Print test result"""
    status = " PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"     {message}")

def test_api_health():
    """Test API health check"""
    print_header("API Health Check")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=TIMEOUT)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_result("Health endpoint", True, f"Status: {data.get('status', 'unknown')}")
            print_result("Database connection", True, f"Articles: {data.get('total_articles', 0)}")
        else:
            print_result("Health endpoint", False, f"HTTP {response.status_code}")
        
        return success
    except Exception as e:
        print_result("Health endpoint", False, str(e))
        return False

def test_articles_endpoint():
    """Test articles endpoint"""
    print_header("Articles Endpoint")
    
    try:
        response = requests.get(f"{API_BASE}/articles?per_page=5", timeout=TIMEOUT)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_result("Articles endpoint", True, f"Retrieved {len(data.get('items', []))} articles")
            print_result("Pagination info", True, f"Page {data.get('page', 0)} of {data.get('pages', 0)}")
            
            # Test individual article structure
            if data.get('items'):
                article = data['items'][0]
                required_fields = ['id', 'title', 'url', 'threat_level', 'source_name']
                missing_fields = [field for field in required_fields if field not in article]
                
                if not missing_fields:
                    print_result("Article structure", True, "All required fields present")
                else:
                    print_result("Article structure", False, f"Missing fields: {missing_fields}")
        else:
            print_result("Articles endpoint", False, f"HTTP {response.status_code}")
        
        return success
    except Exception as e:
        print_result("Articles endpoint", False, str(e))
        return False

def test_search_functionality():
    """Test search functionality"""
    print_header("Search Functionality")
    
    try:
        # Test keyword search
        search_data = {
            "keywords": ["security", "vulnerability"],
            "threat_levels": ["high", "critical"]
        }
        
        response = requests.post(
            f"{API_BASE}/search?per_page=3",
            json=search_data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_result("Search endpoint", True, f"Found {data.get('total', 0)} matching articles")
            
            # Verify search worked
            if data.get('items'):
                sample_article = data['items'][0]
                print_result("Search results", True, f"Sample: {sample_article.get('title', '')[:50]}...")
            
        else:
            print_result("Search endpoint", False, f"HTTP {response.status_code}")
        
        return success
    except Exception as e:
        print_result("Search endpoint", False, str(e))
        return False

def test_statistics():
    """Test statistics endpoint"""
    print_header("Statistics Endpoint")
    
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=TIMEOUT)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_result("Stats endpoint", True, "Statistics retrieved")
            
            # Check required stats
            required_stats = ['total_articles', 'threat_distribution', 'source_distribution']
            for stat in required_stats:
                if stat in data:
                    print_result(f"Stats - {stat}", True, f"Value: {data[stat]}")
                else:
                    print_result(f"Stats - {stat}", False, "Missing from response")
        else:
            print_result("Stats endpoint", False, f"HTTP {response.status_code}")
        
        return success
    except Exception as e:
        print_result("Stats endpoint", False, str(e))
        return False

def test_threat_analysis():
    """Test threat analysis endpoint"""
    print_header("Threat Analysis")
    
    try:
        test_text = {
            "text": "Critical zero-day vulnerability discovered in popular software allows remote code execution. Ransomware groups are actively exploiting this flaw to compromise enterprise networks."
        }
        
        response = requests.post(
            f"{API_BASE}/analyze",
            json=test_text,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_result("Analysis endpoint", True, "Analysis completed")
            print_result("Threat level", True, f"Detected: {data.get('threat_level', 'unknown')}")
            print_result("Confidence score", True, f"Score: {data.get('confidence_score', 0):.2f}")
            
            if data.get('iocs'):
                print_result("IOC extraction", True, f"Found {len(data['iocs'])} IOCs")
            
            if data.get('tags'):
                print_result("Tag extraction", True, f"Tags: {', '.join(data['tags'])}")
        else:
            print_result("Analysis endpoint", False, f"HTTP {response.status_code}")
        
        return success
    except Exception as e:
        print_result("Analysis endpoint", False, str(e))
        return False

def test_manual_scraping():
    """Test manual scraping trigger"""
    print_header("Manual Scraping")
    
    try:
        response = requests.post(f"{API_BASE}/scrape", timeout=TIMEOUT)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            print_result("Scrape trigger", True, data.get('message', 'Triggered'))
        else:
            print_result("Scrape trigger", False, f"HTTP {response.status_code}")
        
        return success
    except Exception as e:
        print_result("Scrape trigger", False, str(e))
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print(f" Starting ChakraWatch Test Suite")
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" API Base: {API_BASE}")
    
    # Wait for server to be ready
    print(f"\n⏳ Waiting for server to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            requests.get(f"{API_BASE}/health", timeout=5)
            print(f"[OK] Server is ready!")
            break
        except:
            if i == max_retries - 1:
                print(f" Server not responding after {max_retries} attempts")
                print(f" Make sure to run: python run.py")
                return False
            time.sleep(1)
            print(f"   Attempt {i+1}/{max_retries}...")
    
    # Run tests
    tests = [
        test_api_health,
        test_articles_endpoint,
        test_search_functionality,
        test_statistics,
        test_threat_analysis,
        test_manual_scraping
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print_result(test.__name__, False, f"Test crashed: {str(e)}")
            results.append(False)
    
    # Summary
    print_header("Test Summary")
    passed = sum(results)
    total = len(results)
    
    print(f" Results: {passed}/{total} tests passed")
    print(f" Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print(f"All tests passed! ChakraWatch is working correctly.")
        print(f"Frontend: Open frontend/index.html in your browser")
        print(f"API Docs: {API_BASE}/docs")
    else:
        print(f" Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
