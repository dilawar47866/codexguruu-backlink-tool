from flask import Flask, render_template, request, jsonify
import requests
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime
import os
from urllib.parse import quote_plus

app = Flask(__name__)
app.secret_key = 'codexguruu-secret-2025'

campaigns = []

FALLBACK_PROSPECTS = {
    "python": [
        {"title": "Real Python - Write for Us", "url": "https://realpython.com/write-for-us/", "snippet": "Python tutorials"},
        {"title": "GeeksforGeeks - Contribute", "url": "https://www.geeksforgeeks.org/contribute/", "snippet": "Programming tutorials"},
        {"title": "DataCamp - Write for Us", "url": "https://www.datacamp.com/community/write-for-datacamp", "snippet": "Data science"},
        {"title": "Towards Data Science", "url": "https://towardsdatascience.com/questions-96667b06af5", "snippet": "Data science publication"},
        {"title": "Analytics Vidhya", "url": "https://www.analyticsvidhya.com/blog/write-for-us/", "snippet": "Data science blog"},
    ],
    "seo": [
        {"title": "Search Engine Journal", "url": "https://www.searchenginejournal.com/write-for-sej/", "snippet": "SEO news"},
        {"title": "Ahrefs Blog", "url": "https://ahrefs.com/blog/write-for-us/", "snippet": "SEO tools blog"},
        {"title": "Moz Blog", "url": "https://moz.com/community/content-guidelines", "snippet": "SEO community"},
        {"title": "Backlinko", "url": "https://backlinko.com/contact", "snippet": "SEO training"},
        {"title": "Search Engine Land", "url": "https://searchengineland.com/guest-author-information", "snippet": "Search marketing"},
    ],
    "wordpress": [
        {"title": "WPBeginner", "url": "https://www.wpbeginner.com/guest-post/", "snippet": "WordPress tutorials"},
        {"title": "Kinsta Blog", "url": "https://kinsta.com/blog/write-for-us/", "snippet": "WordPress hosting"},
        {"title": "DEVELOPER_DEVELOPER Blog", "url": "https://developer.developer.developer.com/blog/", "snippet": "WordPress dev"},
        {"title": "Developer.developer.developer DEV", "url": "https://developer.developer.developer.org/blog/write-for-us/", "snippet": "WordPress plugins"},
    ],
    "coding": [
        {"title": "Dev.to", "url": "https://dev.to/", "snippet": "Developer community"},
        {"title": "FreeCodeCamp", "url": "https://www.freecodecamp.org/news/how-to-contribute/", "snippet": "Coding tutorials"},
        {"title": "CSS Tricks", "url": "https://css-tricks.com/guest-posting/", "snippet": "Web development"},
        {"title": "Smashing Magazine", "url": "https://www.smashingmagazine.com/write-for-us/", "snippet": "Web design"},
        {"title": "SitePoint", "url": "https://www.sitepoint.com/write-for-us/", "snippet": "Web development"},
    ],
    "default": [
        {"title": "Dev.to", "url": "https://dev.to/", "snippet": "Developer community"},
        {"title": "Medium - Write", "url": "https://medium.com/creators", "snippet": "Writing platform"},
        {"title": "Hashnode", "url": "https://hashnode.com/", "snippet": "Developer blogs"},
        {"title": "HackerNoon", "url": "https://hackernoon.com/signup", "snippet": "Tech stories"},
        {"title": "DZone", "url": "https://dzone.com/articles/dzones-article-submission-guidelines", "snippet": "Tech articles"},
    ]
}

def search_duckduckgo(query, max_results=15):
    print(f"  Searching: {query}")
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
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
                
                bad = ["facebook.com", "twitter.com", "pinterest.com", "youtube.com/watch"]
                if any(b in link for b in bad):
                    continue
                
                if link.startswith('http'):
                    results.append({'title': title, 'url': link, 'snippet': snippet})
                    
                if len(results) >= max_results:
                    break
            except:
                continue
        
        print(f"    Found {len(results)} results")
        return results
    except Exception as e:
        print(f"    Search failed: {e}")
        return []

def get_fallback_prospects(niche):
    print(f"  Using fallback database for: {niche}")
    niche_lower = niche.lower()
    
    for key in FALLBACK_PROSPECTS:
        if key in niche_lower:
            return FALLBACK_PROSPECTS[key]
    
    return FALLBACK_PROSPECTS["default"]

def find_prospects(niche):
    queries = [f'{niche} "write for us"', f'{niche} "guest post"']
    
    all_results = []
    seen = set()
    
    print("Starting prospect search...")
    
    for query in queries:
        results = search_duckduckgo(query)
        for r in results:
            domain = r['url'].split('/')[2] if '/' in r['url'] else r['url']
            if domain not in seen:
                seen.add(domain)
                all_results.append(r)
        time.sleep(2)
        if len(all_results) >= 15:
            break
    
    if len(all_results) < 5:
        fallback = get_fallback_prospects(niche)
        for p in fallback:
            domain = p['url'].split('/')[2]
            if domain not in seen:
                seen.add(domain)
                all_results.append(p)
    
    print(f"Total prospects: {len(all_results)}")
    return all_results[:20]

def generate_email(prospect, your_site, niche, api_key):
    prompt = f"""Write a guest post pitch email.

Target: {prospect['title']}
URL: {prospect['url']}
About: {prospect['snippet']}

My site: {your_site}
Niche: {niche}

Requirements:
- Reference their site
- Pitch one article idea
- 120-150 words
- Professional and friendly

Return JSON only:
{{"subject": "subject line", "body": "email body ending with Best, Alex from {your_site}"}}"""

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
        response = r.json()
        text = response["content"][0]["text"]
        
        start = text.find('{')
        end = text.rfind('}') + 1
        return json.loads(text[start:end])
    except Exception as e:
        return {
            "subject": f"Guest Post for {prospect['title'][:30]}",
            "body": f"Hi there,\n\nI found your site and loved your {niche} content.\n\nI'd love to contribute a detailed guide for your readers.\n\nInterested?\n\nBest,\nAlex\n{your_site}"
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start-campaign', methods=['POST'])
def start_campaign():
    data = request.json
    
    if not data.get('anthropic_key') or not data.get('niche'):
        return jsonify({"error": "Missing required fields"}), 400
    
    campaign_id = len(campaigns) + 1
    campaign = {
        "id": campaign_id,
        "your_site": data.get('your_site', 'https://codexguruu.com'),
        "niche": data['niche'],
        "status": "running",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prospects": [],
        "emails": []
    }
    campaigns.append(campaign)
    
    try:
        print(f"\n=== Campaign #{campaign_id} Started ===\n")
        
        prospects = find_prospects(data['niche'])
        campaign['prospects'] = prospects
        
        if not prospects:
            raise Exception("No prospects found")
        
        print(f"\nGenerating {len(prospects)} emails...\n")
        
        for i, prospect in enumerate(prospects, 1):
            print(f"[{i}/{len(prospects)}] {prospect['title'][:50]}...")
            
            try:
                email = generate_email(prospect, campaign['your_site'], data['niche'], data['anthropic_key'])
                
                campaign['emails'].append({
                    "prospect": prospect,
                    "contact": {"write_page": prospect['url']},
                    "subject": email['subject'],
                    "body": email['body'],
                    "status": "ready"
                })
                print(f"  Done")
            except Exception as e:
                print(f"  Skipped: {e}")
            
            time.sleep(2)
        
        campaign['status'] = "completed"
        print(f"\n=== Campaign #{campaign_id}: {len(campaign['emails'])} emails ready ===\n")
        
    except Exception as e:
        campaign['status'] = "failed"
        campaign['error'] = str(e)
        print(f"\nFailed: {e}\n")
    
    return jsonify({"campaign_id": campaign_id, "status": campaign['status']})

@app.route('/campaign/<int:campaign_id>')
def get_campaign(campaign_id):
    campaign = next((c for c in campaigns if c['id'] == campaign_id), None)
    if not campaign:
        return jsonify({"error": "Not found"}), 404
    return jsonify(campaign)

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
