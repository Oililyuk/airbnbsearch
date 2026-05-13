import os
from apify_client import ApifyClient
from openai import OpenAI

# 配置你的 Key
APIFY_TOKEN = "你的_APIFY_TOKEN"
OPENAI_API_KEY = "你的_OPENAI_KEY"  # 也可以指向你本地的 Ollama 地址

# 初始化客户端
apify_client = ApifyClient(APIFY_TOKEN)
ai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_raw_listings(location, limit=10):
    """从 Apify 抓取原始房源数据"""
    run_input = {
        "location": location,
        "maxItems": limit,
        "checkIn": "2026-06-01",  # 示例日期
        "checkOut": "2026-06-05",
    }
    # 使用 Apify 上的 Airbnb Scraper Actor
    run = apify_client.actor("crawlerbros/airbnb-scraper").call(run_input=run_input)
    return list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())

def ai_semantic_filter(listing, criteria):
    """使用 LLM 判断房源是否符合你的个性化定义"""
    description = f"{listing.get('name')} - {listing.get('description', '')}"
    
    prompt = f"""
    你是一个房源筛选助手。用户正在寻找符合以下特征的房源："{criteria}"。
    请分析下方房源的描述，判断它是否真的符合要求。
    
    房源描述：{description}
    
    只需回答：[YES] 或 [NO]，并用一句话说明理由。
    """

    response = ai_client.chat.completions.create(
        model="gpt-4o", # 或者使用 gemma-4
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def main():
    target_location = "Leatherhead, UK"
    my_vibe = "真实的农场体验，有动物（羊或马），且环境安静，非商业化改建的普通公寓。"
    
    print(f"🔍 正在抓取 {target_location} 附近的房源...")
    raw_results = get_raw_listings(target_location, limit=5)
    
    print(f"🤖 正在进行 AI 语义过滤...\n")
    for item in raw_results:
        verdict = ai_semantic_filter(item, my_vibe)
        if "[YES]" in verdict:
            print(f"✅ 符合要求: {item.get('name')}")
            print(f"🔗 链接: https://www.airbnb.com/rooms/{item.get('id')}")
            print(f"📝 AI 理由: {verdict.replace('[YES]', '').strip()}\n")
        else:
            print(f"❌ 过滤掉: {item.get('name')} (原因: {verdict.replace('[NO]', '').strip()})")

if __name__ == "__main__":
    main()