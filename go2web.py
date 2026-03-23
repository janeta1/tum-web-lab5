import hashlib
import json
import os
import sys
import socket
import ssl
import time
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, parse_qs, urlparse

CACHE_DIR = "cache"

def show_help():
    print("Usage:")
    print("  go2web -u <URL>          make an HTTP request to the specified URL")
    print("  go2web -s <search-term>  search the term and print top 10 results")
    print("  go2web -h                show this help")

def url_parse(url):
    scheme, rest = url.split('://')

    if scheme == 'http':
        port = 80
    elif scheme == 'https':
        port = 443
    else:
        raise Exception("Invalid scheme")

    host = rest.split('/')[0]

    if ':' in host:
        host, port = host.split(':')
        port = int(port)

    path = "/" + "/".join(rest.split('/')[1:]) or "/"

    return host, port, path, scheme

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator="\n", strip=True)
    return text

def get_header(headers, name):
    header_lines = headers.splitlines()
    content = ""
    for header in header_lines:
        if header.lower().startswith(name.lower()):
            content = header.split(": ", 1)[1].strip()
    return content

def follow_redirects(status, headers, body, host, scheme, max_redirects):
    if max_redirects == 0:
        print("Error: too many redirects")
        return status, headers, body

    status_code = int(status.split()[1])

    if status_code in (301, 302, 303, 307, 308):
        location = get_header(headers, "Location")
        if location:
            if location.startswith("/"):
                location = f"{scheme}://{host}{location}"
            print(f"-> Redirecting to {location}")
            status, headers, body = fetch(location, max_redirects - 1)
    return status, headers, body

def get_cache_path(url):
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{url_hash}.json")

def load_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    return None

def save_cache(cache_file, new_entry):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(new_entry, f, indent=2)

def get_from_cache(url):
    cache_file = get_cache_path(url)
    entry = load_cache(cache_file)
    if entry and time.time() - entry["timestamp"] < 3600:
        return entry
    return None

def add_to_cache(url, status, headers, body):
    cache_file = get_cache_path(url)
    entry = {
        "status": status,
        "headers": headers,
        "body": body,
        "timestamp": time.time()
    }
    save_cache(cache_file, entry)

def display(headers, body):
    content_type = get_header(headers, "Content-Type")
    if "application/json" in content_type:
        try:
            parsed = json.loads(body) # json string to dict
            print(json.dumps(parsed, indent=2)) # dict to json string
        except json.decoder.JSONDecodeError:
            print(body)
    else:
        print(parse_html(body))

def fetch(url, max_redirects=10):
    host, port, path, scheme = url_parse(url)

    cached= get_from_cache(url)
    if cached:
        print(f"-> Served from cache: {url}")
        return cached["status"], cached["headers"], cached["body"]

    request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\nUser-Agent: go2web/1.0\r\nAccept: application/json, text/html\r\nConnection: close\r\n\r\n"

    print(f"-> Fetching {url}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    if port == 443:
        context = ssl.create_default_context()
        s = context.wrap_socket(s, server_hostname=host)


    s.sendall(request.encode())

    response = b""
    while True:
        chunk = s.recv(1024)
        if not chunk:
            break
        response += chunk
    s.close()

    header_data, _, body = response.partition(b'\r\n\r\n')
    headers = header_data.decode()
    status_line = headers.splitlines()[0]

    status, headers, body = follow_redirects(status_line, headers, body, host, scheme, max_redirects)
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    add_to_cache(url, status, headers, body)
    return status, headers, body

def search(term):
    print(f"-> Searching for {term}...")
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(term)}" # converts words into URL-safe
    status, headers, body = fetch(url)

    if "200" not in status:
        print(f"Search failed: {status}")
        return

    soup = BeautifulSoup(body, 'html.parser')
    results = soup.find_all('a', class_="result__a", limit=10)
    print("\n")

    for i, result in enumerate(results, 1):
        raw = result.get('href')
        parsed = urlparse(raw) # breaks into parts - scheme, host, path, query
        qs = parse_qs(parsed.query) # turns the raw query string into a dict
        real_url = qs['uddg'][0] if 'uddg' in qs else raw

        print(f"{i}. {result.get_text()}")
        print(f"    {real_url}")
        print()

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "-h":
        show_help()
        return

    if sys.argv[1] == "-u":
        if len(sys.argv) < 3:
            print("Error: -u requires a URL")
            sys.exit(1)
        url = sys.argv[2]
        status, headers, body = fetch(url)
        print("\n-------------------------")
        print(f"Status: {status}")
        print("-------------------------")
        display(headers, body)
        return

    if sys.argv[1] == "-s":
        if len(sys.argv) < 3:
            print("Error: -s requires a search term")
            sys.exit(1)
        term = " ".join(sys.argv[2:])
        search(term)
        return

    print(f"Unknown option: {sys.argv[1]}")
    sys.exit(1)

if __name__ == "__main__":
    main()