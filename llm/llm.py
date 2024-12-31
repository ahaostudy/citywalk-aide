import os

from dotenv import load_dotenv
from openai import OpenAI

from model.route import LLMRoutes, LLMRoute

load_dotenv()

API_KEY = os.getenv('OPENAI_API_KEY')
BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')


def chat(content: str, system: str = '', json_schema=None) -> str:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    if json_schema:
        response = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content}
            ],
            response_format=json_schema,
        )
    else:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content}
            ]
        )

    result = response.choices[0].message.content
    return result


if __name__ == '__main__':
    routes_raw = chat(
        content="""
天津一日游
行程：
🕖 早上7:20 北京出发，🕗 8:00 到天津站
8:00-8:30
从高铁出站后，从站前广场这边出站，往外走，就能看到解放桥和世纪钟，很近。
🆓 免费游览
⏰ 世纪钟～为了迎接21世纪而建造的大型城市雕塑 🕰️
⛩️ 解放桥～清光绪二十七年（1901年）6月12日，八国联军法军将军华伦提议修建铁桥，桥梁将永远对中外人士开放，因此命名为“万国桥”。1949年更名为解放桥。
🌊 海河～解放桥下的海河，京杭大运河的一部分
8:30-10:00
8:30左右开始，从解放桥走路15分钟，跟着导航走到意大利风情街 🍝：
🆓 免费游览
曾经的意大利租界，1947年，我国正式收回。
10:00-10:30
10:00出了风情街，步行5分钟就是北安桥！很漂亮！🌉
🆓 免费游览
桥头雕塑采用西洋古典表现形式，青龙、白虎、朱雀、玄武，寓意东南西北四方平安。
10:30-11:00
10:30从北安桥下来，走路20分钟，到瓷房子 🏺。
📸 拍照即可，门票50元
周围还有张学良故居和张爱玲故居 🎫。
11:00-13:00
午餐🥣➕休整在恒隆广场 🛍️。
13:00-15:00
13:00开始，骑车15分钟到五大道 🚴‍♂️，选了25元/人的人工讲解 🎧。
五大道～由五条大道组成，曾经的英租界，有各式各样的小洋楼，去民园广场打卡小罗马体育场。
15:00-16:00
15:00开始骑车10分钟到西开教堂⛪️罗曼史风格。
🆓 免费游览
16:00-17:00 (可选活动)
如果体力允许，16:00左右骑车20分钟到鼓楼&古文化街溜达 🐉。
17:00-18:30
17:00左右骑车11分钟到天津之眼 🎡，晚餐🍲
18:30 onwards
打车大概10分钟到天津西站 🚕。
🕖 火车19:00后，结束天津之旅啦～ 👋
""",
        system="""
Parse the articles shared by users into structured Citywalk route data. Each article may correspond to multiple routes:
1.	Route: Each route contains multiple locations and basic information about the route, such as name, summary, etc.;
2.	Location: Each location contains a lot of basic information and may also include the following data:
    a.	Activities: Activities at the location, explaining what should be done at the current location, such as visiting, playing games, eating, etc.;
    b.	Transportation: Instructions on how to get to the location.
Notes:
1.	The content should be in Chinese;
2.	Strict numerical information not mentioned in the article, such as latitude and longitude, ticket fees, etc., should not be generated;
3.	For non-strict information, such as location descriptions, approximate visiting times, etc., if available, must be generated; if not, it can be freely created.
""",
        json_schema=LLMRoutes
    )
    print(routes_raw)

    routes = LLMRoutes.model_validate_json(routes_raw)
    for route in routes.routes:
        r, ls = route.to_route_model()
        print(r.to_dict(), [l.to_dict() for l in ls])
