# This script updates the Jita market data in the database using the ESI API.

import requests

def fetch_jita_market_data(page=1):
    url = f"https://esi.evetech.net/latest/markets/10000002/orders/?datasource=tranquility&order_type=sell&page={page}"
    response = requests.get(url)
    if response.status_code == 200:
        return response
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

# timer function to measure execution time
def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.2f} seconds")
        return result
    return wrapper

@timer
def fetch_all_jita_market_data(all_pages=0)-> list:
    """
    Fetch all Jita market data from the ESI API.
    If all_pages is set to 0, it will fetch only the first page.
    If all_pages is set to a positive integer, it will fetch that many pages.
    """
    all_data = []
    if all_pages <= 0:
        return [fetch_jita_market_data(1)]
    
    for page in range(1, all_pages + 1):
        print(f"Fetching page {page} of {all_pages}")
        page_data = fetch_jita_market_data(page)
        if page_data is not None:
            all_data.append(page_data.json())
        else:
            print(f"Failed to fetch data for page {page}")
    
    return all_data

if __name__ == "__main__":
    # get the market data / wait for response
    jita_market_data = fetch_jita_market_data()
    # check for pages
    if jita_market_data is not None:
        print(f"Need to send {jita_market_data.headers['X-Pages']} more requests to get all pages")
        # get the number of pages
        pages = int(jita_market_data.headers['X-Pages'])
        # fetch all pages
        all_jita_market_data = fetch_all_jita_market_data(pages)
        print(f"Fetched {len(all_jita_market_data)} pages of Jita market data.")

