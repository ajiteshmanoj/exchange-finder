import requests
import json

url = "http://localhost:8000/api/search"

# CORRECTED PAYLOAD - just module codes as strings
payload = {
    "credentials": {
        "username": "AJITESH001",
        "password": "Ajite$h08122003",
        "domain": "Student"
    },
    "exchange_semester": "Y3S1",
    "target_modules": [
        "SC4001",  # Just the code, not an object
        "SC4002",
        "SC4062",
        "SC4021",
        "SC4023",
        "SC4003"
    ],
    "preferred_countries": [
        "Australia", "Denmark", "Finland", 
        "Ireland", "Netherlands", "Norway", "Sweden"
    ],
    "student_cgpa": 3.75,
    "min_mappable_modules": 2
}

print("🔍 Searching with YOUR actual criteria...")
print(f"   Countries: {len(payload['preferred_countries'])} countries")
print(f"   Modules: {len(payload['target_modules'])} modules")
print(f"   Min mappable: {payload['min_mappable_modules']}")
print("\n⏳ This will take 15-25 minutes (scraping ~45 universities)...\n")

try:
    response = requests.post(url, json=payload, timeout=1800)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"\n❌ ERROR: API returned status {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)
    
    result = response.json()
    
    if 'detail' in result:
        print(f"\n❌ API Error: {result['detail']}")
        exit(1)
    
    if 'total_found' not in result:
        print(f"\n❌ Unexpected response format:")
        print(json.dumps(result, indent=2))
        exit(1)
    
    print(f"\n✅ Found {result['total_found']} universities!")
    print(f"⏱️  Search time: {result['search_time_seconds']/60:.1f} minutes\n")

    from collections import defaultdict
    by_country = defaultdict(list)

    for uni in result['universities']:
        by_country[uni['country']].append(uni)

    for country in sorted(by_country.keys()):
        unis = by_country[country]
        print(f"\n{'='*60}")
        print(f"🌍 {country.upper()} ({len(unis)} universities)")
        print('='*60)
        
        for uni in unis[:3]:
            print(f"\n{uni['rank']}. {uni['university_name']}")
            print(f"   ✅ {uni['mappable_count']}/{len(payload['target_modules'])} modules mappable ({uni['coverage_percentage']:.0f}%)")
            print(f"   👥 {uni['spots_available']} spots | 📊 Min CGPA: {uni['min_cgpa']}")
            
            for m in uni['mappable_modules'][:3]:
                print(f"      • {m['ntu_code']} → {m['partner_code']}")
            
            if len(uni['mappable_modules']) > 3:
                print(f"      ... and {len(uni['mappable_modules'])-3} more")

    print("\n" + "="*60)
    print(f"💾 All {result['total_found']} results cached for instant future searches!")
    print("="*60)

except requests.exceptions.Timeout:
    print("\n❌ Request timed out after 30 minutes")
except requests.exceptions.ConnectionError:
    print("\n❌ Cannot connect to API. Is the server running?")
    print("   Run: python run_api.py")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    print(f"\nFull response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)