import sys
import asyncio

from async_crawler import crawl_site_async


async def main() -> None:
    args = sys.argv

    if len(args) < 2:
        print("no website provided")
        exit(1)

    if len(args) > 2:
        print("too many arguments provided")
        exit(1)

    base_url = args[1]
    print(f"starting crawl of: {base_url}...")

    page_data = await crawl_site_async(base_url, 10)

    print(f"Found {len(page_data)} pages:")
    for page in page_data.values():
        print(f"- {page['url']}: {len(page['outgoing_links'])} outgoing links")

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
