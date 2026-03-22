import re
import sys
import socket
import ssl
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, unquote, parse_qs, urlparse

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

    return host, port, path


def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator="\n", strip=True)
    return text

def fetch(url):
    host, port, path = url_parse(url)

    request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\nConnection: close\r\n\r\n"

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
    return status_line, headers, body.decode()


def search(term):
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(term)}" # converts words into URL-safe
    status, headers, body = fetch(url)

    if "200" not in status:
        print(f"Search failed: {status}")
        return

    soup = BeautifulSoup(body, 'html.parser')
    results = soup.find_all('a', class_="result__a", limit=10)

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
            return
        url = sys.argv[2]
        status, headers, body = fetch(url)
        print("-------------------------")
        print(f"Status: {status}")
        print("-------------------------")
        print(parse_html(body))
        return

    if sys.argv[1] == "-s":
        if len(sys.argv) < 3:
            print("Error: -s requires a search term")
            return
        term = " ".join(sys.argv[2:])
        search(term)
        return

    print(f"Unknown option: {sys.argv[1]}")

if __name__ == "__main__":
    main()