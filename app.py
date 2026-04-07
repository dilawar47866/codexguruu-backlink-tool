from flask import Flask, render_template, request, jsonify
import requests
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime
import os
from urllib.parse import quote_plus
import threading

app = Flask(__name__)
app.secret_key = 'codexguruu-secret-2025'

campaigns = []

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# Fallback prospect database
FALLBACK_PROSPECTS = {
    "python": [
        {"title": "Real Python - Write for Us", "url": "https://realpython.com/write-for-us/", "snippet": "Python tutorials and guides"},
        {"title": "GeeksforGeeks - Contribute", "url": "https://www.geeksforgeeks.org/contribute/", "snippet": "Programming tutorials"},
        {"title": "DataCamp - Write for Us", "url": "https://www.datacamp.com/community/write-for-datacamp", "snippet": "Data science tutorials"},
        {"title": "Towards Data Science", "url": "https://towardsdatascience.com/questions-96667b06af5", "snippet": "Data science publication"},
        {"title": "Analytics Vidhya", "url": "https://www.analyticsvidhya.com/blog/write-for-us/", "snippet": "Data science and AI blog"},
        {"title": "Python Land - Guest Posts", "url": "https://python.land/write-for-us", "snippet": "Python programming tutorials"},
        {"title": "Full Stack Python", "url": "https://www.fullstackpython.com/contribute.html", "snippet": "Python web development"},
    ],
    "seo": [
        {"title": "Search Engine Journal - Write for Us", "url": "https://www.searchenginejournal.com/write-for-sej/", "snippet": "SEO and digital marketing news"},
        {"title": "Ahrefs Blog - Guest Posts", "url": "https://ahrefs.com/blog/write-for-us/", "snippet": "SEO tools and strategies"},
        {"title": "Moz Blog - Community", "url": "https://moz.com/community/content-guidelines", "snippet": "SEO community guidelines"},
        {"title": "Backlinko - Contact", "url": "https://backlinko.com/contact", "snippet": "SEO training and link building"},
        {"title": "Search Engine Land", "url": "https://searchengineland.com/guest-author-information", "snippet": "Search marketing news"},
        {"title": "SEMrush Blog", "url": "https://www.semrush.com/blog/write-for-semrush/", "snippet": "Digital marketing blog"},
    ],
    "wordpress": [
        {"title": "WPBeginner - Guest Post", "url": "https://www.wpbeginner.com/guest-post/", "snippet": "WordPress tutorials for beginners"},
        {"title": "Kinsta Blog - Write for Us", "url": "https://kinsta.com/blog/write-for-us/", "snippet": "WordPress hosting and performance"},
        {"title": "WP Tavern - Contact", "url": "https://wptavern.com/contact", "snippet": "WordPress news and updates"},
        {"title": "WPMU DEV Blog", "url": "https://wpmudev.com/blog/write-for-us/", "snippet": "WordPress development and plugins"},
        {"title": "WPKube - Write for Us", "url": "https://www.wpkube.com/write-for-us/", "snippet": "WordPress resources"},
    ],
    "coding": [
        {"title": "Dev.to - Write Posts", "url": "https://dev.to/", "snippet": "Developer community platform"},
        {"title": "FreeCodeCamp - Contribute", "url": "https://www.freecodecamp.org/news/how-to-contribute/", "snippet": "Coding tutorials and guides"},
        {"title": "CSS Tricks - Guest Posting", "url": "https://css-tricks.com/guest-posting/", "snippet": "Web development blog"},
        {"title": "Smashing Magazine - Write for Us", "url": "https://www.smashingmagazine.com/write-for-us/", "snippet": "Web design and development"},
        {"title": "SitePoint - Write for Us", "url": "https://www.sitepoint.com/write-for-us/", "snippet": "Web development tutorials"},
        {"title": "Hashnode", "url": "https://hashnode.com/", "snippet": "Blogging platform for developers"},
        {"title": "HackerNoon - Submit Story", "url": "https://hackernoon.com/signup", "snippet": "Tech stories and tutorials"},
    ],
    "web development": [
        {"title": "CSS Tricks", "url": "https://css-tricks.com/guest-posting/", "snippet": "Frontend development"},
        {"title": "Smashing Magazine", "url": "https://www.smashingmagazine.com/write-for-us/", "snippet": "Web design"},
        {"title": "A List Apart", "url": "https://alistapart.com/about/contribute/", "snippet": "Web standards"},
        {"title": "Codrops - Submit", "url": "https://tympanus.net/codrops/advertise/", "snippet": "Web design inspiration"},
        {"title": "SitePoint", "url": "https://www.sitepoint.com/write-for-us/", "snippet": "Web development"},
    ],
    "default": [
        {"title": "Dev.to", "url": "https://dev.to/", "snippet": "Developer community"},
        {"title": "Medium - Write", "url": "https://medium.com/creators", "snippet": "Writing platform"},
        {"title": "Hashnode", "url": "https://hashnode.com/", "snippet": "Developer blogs"},
        {"title": "HackerNoon", "url": "https://hackernoon.com/signup", "snippet": "Tech stories"},
        {"title": "DZone", "url": "https://dzone.com/articles/dzones-article-submission-guidelines", "snippet": "Tech articles"},
        {"title": "FreeCodeCamp", "url": "https://www.freecodecamp.org/news/how-to-contribute/", "snippet": "Coding tutorials"},
    ]
}

def search_duckduckgo(query, max_results=15):
    """Search DuckDuckGo for prospects"""
    print(f"  Searching: {query}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for result in soup.find_all('div', class_='result'):
            try:
                title_elem = result.find('a', class_='result__a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')
                
                snippet_elem = result.find('a', class_='result__snippet')
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                # Filter bad domains
                bad_domains = ["facebook.com", "twitter.com", "pinterest.com", "youtube.com/watch", "instagram.com"]
                if any(bad in link for bad in bad_domains):
                    continue
                
                if link.startswith('http'):
                    results.append({
                        'title': title,
                        'url': link,
                        'snippet': snippet,
                        'date': 'Recent'
                    })
                    
                if len(results) >= max_results:
                    break
                    
            except Exception as e:
                continue
        
        print(f"    Found {len(results)} results")
        return results
        
    except Exception as e:
        print(f"    Search failed: {e}")
        return []

def get_fallback_prospects(niche):
    """Get curated prospects from database"""
    print(f"  Using fallback database for: {niche}")
    
    niche_lower = niche.lower()
    
    # Try to match niche to database
    for key in FALLBACK_PROSPECTS:
        if key in niche_lower:
            print(f"    Matched category: {key}")
            return FALLBACK_PROSPECTS[key]
    
    # Return default if no match
    print(f"    Using default category")
    return FALLBACK_PROSPECTS["default"]

def find_prospects(niche):
    """Find guest post prospects"""
    
    queries = [
        f'{niche} "write for us"',
        f'{niche} "guest post"'
    ]
    
    all_results = []
    seen_domains = set()
    
    print("Starting prospect search...")
    
    # Try DuckDuckGo search first
    for query in queries:
        results = search_duckduckgo(query, max_results=15)
        
        for r in results:
            try:
                domain = r['url'].split('/')[2] if '/' in r['url'] else r['url']
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    all_results.append(r)
            except:
                continue
        
        time.sleep(2)  # Be nice to DuckDuckGo
        
        if len(all_results) >= 15:
            break
    
    # Add fallback prospects if not enough results
    if len(all_results) < 10:
        print(f"\n  Only found {len(all_results)} from search, adding curated prospects...")
        fallback = get_fallback_prospects(niche)
        
        for prospect in fallback:
            try:
                domain = prospect['url'].split('/')[2]
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    all_results.append(prospect)
            except:
                continue
    
    print(f"\nTotal prospects found: {len(all_results)}\n")
    return all_results[:20]  # Return max 20

def generate_email(prospect, your_site, niche, api_key):
    """Generate personalized email using Claude"""
    
    prompt = f"""Write a personalized guest post pitch email.

TARGET SITE:
- Title: {prospect['title']}
- URL: {prospect['url']}
- About: {prospect['snippet']}

MY DETAILS:
- Website: {your_site}
- Niche: {niche}

REQUIREMENTS:
- Reference their site specifically (mention their title or focus area)
- Pitch ONE concrete article idea related to {niche}
- Keep it 120-150 words total
- Sound professional but friendly and human
- No generic templates

Return ONLY this exact JSON format (no other text):
{{"subject": "your subject line here", "body": "email body here ending with\\n\\nBest,\\nAlex\\n{your_site}"}}"""

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "temperature": 0.85,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=30)
        
        if r.status_code != 200:
            raise Exception(f"API returned status {r.status_code}")
        
        response = r.json()
        
        if "content" not in response:
            raise Exception("Invalid API response")
        
        text = response["content"][0]["text"]
        
        # Extract JSON from response
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start == -1 or end == 0:
            raise Exception("No JSON found in response")
        
        json_str = text[start:end]
        email_data = json.loads(json_str)
        
        # Validate required fields
        if "subject" not in email_data or "body" not in email_data:
            raise Exception("Missing subject or body in response")
        
        return email_data
        
    except Exception as e:
        print(f"    Claude API error: {e}, using fallback")
        
        # Fallback email template
        site_name = prospect['title'].split('-')[0].strip()
        
        return {
            "subject": f"Guest Post Idea for {site_name}",
            "body": f"""Hi there,

I came across {site_name} while researching {niche} resources and really enjoyed your content on {prospect['snippet'][:50]}.

I'd love to contribute a comprehensive, data-driven guide that I think would resonate with your audience - something practical and actionable based on real-world experience.

Would you be open to discussing a pitch?

Best,
Alex
{your_site}"""
        }

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/start-campaign', methods=['POST', 'OPTIONS'])
def start_campaign():
    """Start a new backlink campaign"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        if not data.get('anthropic_key'):
            return jsonify({"error": "Anthropic API key is required"}), 400
        
        if not data.get('niche'):
            return jsonify({"error": "Niche is required"}), 400
        
        campaign_id = len(campaigns) + 1
        campaign = {
            "id": campaign_id,
            "your_site": data.get('your_site', 'https://codexguruu.com'),
            "niche": data['niche'],
            "status": "running",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prospects": [],
            "emails": [],
            "error": None
        }
        campaigns.append(campaign)
        
        # Process campaign in background thread
        def process_campaign():
            try:
                print(f"\n{'='*60}")
                print(f"Campaign #{campaign_id} Started")
                print(f"Niche: {data['niche']}")
                print(f"{'='*60}\n")
                
                # Find prospects
                prospects = find_prospects(data['niche'])
                campaign['prospects'] = prospects
                
                if not prospects:
                    campaign['status'] = "failed"
                    campaign['error'] = "No prospects found. Try a different niche like 'Python' or 'SEO'."
                    return
                
                print(f"\nGenerating {len(prospects)} personalized emails...\n")
                
                # Generate emails
                for i, prospect in enumerate(prospects, 1):
                    try:
                        print(f"[{i}/{len(prospects)}] {prospect['title'][:50]}...")
                        
                        email = generate_email(
                            prospect,
                            campaign['your_site'],
                            data['niche'],
                            data['anthropic_key']
                        )
                        
                        campaign['emails'].append({
                            "prospect": prospect,
                            "contact": {"write_page": prospect['url']},
                            "subject": email['subject'],
                            "body": email['body'],
                            "status": "ready"
                        })
                        
                        print(f"  ✓ Done")
                        
                    except Exception as e:
                        print(f"  ✗ Skipped: {e}")
                        continue
                    
                    time.sleep(2)  # Rate limiting
                
                campaign['status'] = "completed"
                print(f"\n{'='*60}")
                print(f"Campaign #{campaign_id} Complete!")
                print(f"Generated {len(campaign['emails'])} emails")
                print(f"{'='*60}\n")
                
            except Exception as e:
                campaign['status'] = "failed"
                campaign['error'] = str(e)
                print(f"\nCampaign #{campaign_id} failed: {e}\n")
        
        # Start background thread
        thread = threading.Thread(target=process_campaign)
        thread.daemon = True
        thread.start()
        
        # Return immediately
        return jsonify({
            "campaign_id": campaign_id,
            "status": "running",
            "message": "Campaign started successfully"
        }), 200
        
    except Exception as e:
        print(f"Error in start_campaign: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/campaign/<int:campaign_id>')
def get_campaign(campaign_id):
    """Get campaign status and results"""
    
    campaign = next((c for c in campaigns if c['id'] == campaign_id), None)
    
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    
    return jsonify(campaign), 200

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "campaigns": len(campaigns)}), 200

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("🚀 CODEXGURUU BACKLINK MACHINE")
    print("="*60)
    print(f"✅ Server starting on port {port}")
    print("✅ DuckDuckGo search + curated database")
    print("✅ Claude AI email generation")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)
