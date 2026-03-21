import sys
import socket
import ssl

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
    print(f"Status: {status_line}")
    print(body.decode())


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "-h":
        show_help()
        return

    if sys.argv[1] == "-u":
        if len(sys.argv) < 3:
            print("Error: -u requires a URL")
            return
        url = sys.argv[2]
        fetch(url)
        return

    if sys.argv[1] == "-s":
        if len(sys.argv) < 3:
            print("Error: -s requires a search term")
            return
        term = " ".join(sys.argv[2:])
        print(f"[TODO] Implement search for {term}")
        return

    print(f"Unknown option: {sys.argv[1]}")

if __name__ == "__main__":
    main()