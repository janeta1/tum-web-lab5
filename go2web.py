import sys

def show_help():
    print("Usage:")
    print("  go2web -u <URL>          make an HTTP request to the specified URL")
    print("  go2web -s <search-term>  search the term and print top 10 results")
    print("  go2web -h                show this help")


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "-h":
        show_help()
        return

    if sys.argv[1] == "-u":
        if len(sys.argv) < 3:
            print("Error: -u requires a URL")
            return
        url = sys.argv[2]
        print(f"[TODO] Implement fetch {url}")
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