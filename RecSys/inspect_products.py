import asyncio
from recommendation_model_API import fetch_products_from_supabase

async def inspect():
    print("Fetching products...")
    products = await fetch_products_from_supabase()
    print(f"Fetched {len(products)} products.")
    
    print("\nSample products:")
    count = 0
    for pid, info in products.items():
        print(f"[{pid}] {info}")
        count += 1
        if count >= 10:
            break

if __name__ == "__main__":
    asyncio.run(inspect())
