import requests
from bs4 import BeautifulSoup
import re
import json
import os
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

#創建Flask物件app并初始化
app = Flask(__name__)

# 啟用 Flask-CORS，允許指定的前端 URL
CORS(app, resources={r"/fetch_recipes": {"origins": "https://final-projrct-5us7.onrender.com"}})

@app.route('/')
def home():
    return jsonify({"message": "Welcome!"})


#app的路由地址"/fetch_recipes"即為ajax中定義的url地址，采用POST提交
@app.route('/fetch_recipes',methods=["POST", "OPTIONS"])
#從這里定義具體的函式 回傳值均為json格式
def fetch_recipes():
    base_url = "https://icook.tw/recipes/search?q={}&page={}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    if request.method == "OPTIONS":
        # 處理 CORS 預檢請求
        response = jsonify({"message": "CORS preflight check OK"})
        response.headers.add("Access-Control-Allow-Origin", "https://final-projrct-5us7.onrender.com")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response
    
    all_recipes = []
    max_recipes = 5  # 设置最大爬取的食谱数量

    data = request.get_json()  # 获取请求体
    print("Raw data from request:", request.data)  # 打印原始請求數據
    print("Parsed JSON data:", data)  # 打印解析後的 JSON 數據

    if not data:
        return jsonify({"error": "Invalid JSON format"}), 400

    print("Received data:", data)  # 打印数据

    ingredients = data.get('ingredients', [])
    if not ingredients:
            return jsonify({"error": "No ingredients provided"}), 400
    print("Received requesto with ingredients:", request.json.get('ingredients'))  # 调试日志
    

    # 连接 PostgreSQL 数据库
    conn = psycopg2.connect(
        dbname="recipes_u4hs",
        user="recipes_u4hs_user",
        password="lVj411CBNPInWeJ3z6DRwZprm0sQCGSQ",
        host="dpg-cto0nkrqf0us73akml30-a.singapore-postgres.render.com",
        port="5432"
    )
    cur = conn.cursor()

    # 创建表（如果不存在）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id SERIAL PRIMARY KEY,
            recipe_name TEXT NOT NULL,
            url TEXT,
            ingredients TEXT,
            recipe_detail TEXT,
            image TEXT
        );
        """)
    conn.commit()


    for ingredient in ingredients:
        recipe_count = 0  # 用于记录当前爬取的食谱数量
        for page in range(1, 2):  # 假設只爬取每個食材的前一頁
            
            if recipe_count >= max_recipes:
                break  # 达到最大数量时退出循环

            try:
                res = requests.get(url=base_url.format(ingredient, page), headers=headers, timeout=10)
                res.raise_for_status()  # 檢查請求是否成功
            except requests.RequestException as e:
                print(f"Error fetching page {page} for ingredient {ingredient}: {e}")
                continue

            soup = BeautifulSoup(res.content, 'html.parser')
            recipes_obj = soup.select('li[class="browse-recipe-item"]')

            for recipe in recipes_obj:
                if recipe_count >= max_recipes:
                    break  # 再次检查，确保退出
                
                try:
                    recipe_data = {}

                    # 食譜名稱
                    title = recipe.select_one('h2.browse-recipe-name')
                    if title:
                        recipe_name = title.text.strip()
                        recipe_name = re.sub(r"[\\\\/:*?\"<>|]", "", recipe_name)[:20]
                        recipe_data["RecipeName"] = recipe_name

                    # 食譜網址
                    link = recipe.select_one('a')
                    if link:
                        recipe_url = "https://icook.tw" + link["href"]
                        recipe_data["Url"] = recipe_url

                        # 詳細內容
                        try:
                            content_res = requests.get(url=recipe_url, headers=headers, timeout=10)
                            content_res.raise_for_status()  # 檢查請求是否成功
                        except requests.RequestException as e:
                            print(f"Error fetching recipe details from {recipe_url}: {e}")
                            continue

                        content_soup = BeautifulSoup(content_res.content, 'html.parser')

                        # 食材
                        ingredients_obj = content_soup.select('li.ingredient')
                        ingredients_data = [
                            f'{i.select_one("div.ingredient-name a").text.strip()} {i.select_one("div.ingredient-unit").text.strip()}'
                            for i in ingredients_obj
                        ]
                        recipe_data["Ingredients"] = ingredients_data

                        # 步驟
                        steps_data = ['{}. '.format(n+1) + x.text
                                        for n, x in enumerate(content_soup.select('li > figure > figcaption > p'))]  # 按tag依序找出
                        recipe_data["RecipeDetail"] = "\n".join(steps_data)

                        # 圖片
                        image = content_soup.select_one('img.recipe-cover')
                        if image:
                            recipe_data["Image"] = image["src"]
                    # 插入数据到 PostgreSQL
                    cur.execute("""
                    INSERT INTO recipes (recipe_name, url, ingredients, recipe_detail, image)
                    VALUES (%s, %s, %s, %s, %s);
                    """, (
                        recipe_data.get("RecipeName"),
                        recipe_data.get("Url"),
                        recipe_data.get("Ingredients"),
                        recipe_data.get("RecipeDetail"),
                        recipe_data.get("Image")
                    ))
                    conn.commit()


                    all_recipes.append(recipe_data)
                    recipe_count += 1  # 增加计数器

                    print(f"食譜::{recipe_data}")
                except Exception as e:
                    print(f"Error processing recipe: {e}")
                    continue
            if recipe_count >= max_recipes:
                break  # 检查总数后退出外层循环
    # 关闭数据库连接
    cur.close()
    conn.close()

    return jsonify(all_recipes),200
    
    # 儲存到 JSON 檔案
    #output_path = os.path.join(os.path.dirname(__file__), '../src/recipe.json')
    #with open(output_path, 'w', encoding='utf-8') as f:
    #    json.dump(all_recipes, f, ensure_ascii=False, indent=4)

    

# 測試函數
if __name__ == "__main__":
    app.run(host="127.0.0.1",port=5000,debug=True)
