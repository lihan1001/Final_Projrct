# icook recipe scraper
import requests
from bs4 import BeautifulSoup
import os
import re
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
#-----------------------------------------------------------------
#從網頁抓取爬取食材(新)

app = Flask(__name__)
CORS(app)  # 允許所有來源的請求

@app.route('/fetch_recipes', methods=['POST'])
def fetch_recipes():
    try:
        ingredients = request.json.get("ingredients", [])
        if not ingredients:
            return jsonify({"error": "No ingredients provided"}), 400

        headers = {
            'content-type': 'text/html; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
        }

        base_url = 'https://icook.tw/search/食材：{}/?page={}'
        all_recipes = []

        for ingredient in ingredients:
            for page in range(1, 3):  # 假設只爬取每個食材的前兩頁
                res = requests.get(url=base_url.format(ingredient, page), headers=headers)
                soup = BeautifulSoup(res.content, 'html.parser')
                recipes_obj = soup.select('li[class="browse-recipe-item"]')

                for recipe in recipes_obj:
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
                            content_res = requests.get(url=recipe_url, headers=headers)
                            content_soup = BeautifulSoup(content_res.content, 'html.parser')

                            # 食材
                            ingredients_obj = content_soup.select('div[class="ingredient"]')
                            recipe_data["Ingredients"] = [
                                f'{i.select_one("a").text.strip()} {i.select_one("div.ingredient-unit").text.strip()}'
                                for i in ingredients_obj
                            ]

                            # 作法
                            steps_obj = content_soup.select('ul.recipe-details-steps p.recipe-step-description-content')
                            recipe_data["RecipeDetail"] = "\n".join([step.text.strip() for step in steps_obj])

                        if recipe_data.get("RecipeName") and recipe_data.get("Url"):
                            all_recipes.append(recipe_data)

                    except Exception as e:
                        print(f"Error processing recipe: {e}")
                        continue

        # 儲存到 JSON 檔案
        output_path = './icook/recipe.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_recipes, f, ensure_ascii=False, indent=4)

        return jsonify({"message": "Recipes fetched successfully", "recipe_count": len(all_recipes)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)  # 明確使用 0.0.0.0 支持所有網卡

#-----------------------------------------------------------------
#從程式端輸入爬取食材(舊)

# vegetable = input("請輸入想查詢的蔬菜名稱:")
# headers = {
#     'content-type': 'text/html; charset=UTF-8',
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
# }

# # url = 'https://icook.tw/search/%E9%A3%9F%E6%9D%90%EF%BC%9A%E7%AB%B9%E7%AD%8D/?page={}'

# url = 'https://icook.tw/search/食材：{}/?page={}'

# page_scraped = int(input("請問想爬幾頁食譜(請輸入阿拉伯數字):"))
# page = 1

# all_recipes = []  # 用於存放所有食譜

# for i in range(0, page_scraped):
#     res = requests.get(url=url.format(vegetable, page), headers=headers)
#     html = res.content
#     soup = BeautifulSoup(html, 'html.parser')
#     # print(soup)

#     recipes_Obj = soup.select('li[class="browse-recipe-item"]')  # <class 'bs4.element.ResultSet'>
#     for recipes in recipes_Obj:
#         recipe_ingredient = {}  # 每次迭代建立一個新的字典

#         try:
#             # 取得食譜標題
#             titles = recipes.select('h2[class="browse-recipe-name"]')
#             for titleName in titles:
#                 recipeName = titleName.text.strip()
#                 pattern = r"[\\\\/:*?\"<>|]"
#                 recipeName = re.sub(pattern, "", recipeName)[:20]
#                 recipe_ingredient["RecipeName"] = recipeName

#             # 取得食譜內文網址
#             contents = recipes.select('a')
#             for content in contents:
#                 contentUrl = "https://icook.tw" + content["href"]
#                 recipe_ingredient["Url"] = contentUrl

#                 # 取得食譜詳細內容
#                 content_res = requests.get(url=contentUrl, headers=headers)
#                 content_soup = BeautifulSoup(content_res.content, 'html.parser')

#                 # 食材列表
#                 ingredients_Obj = content_soup.select('div[class="ingredient"]')
#                 recipe_ingredient["Ingredients"] = [
#                     ingredient.select_one('a').text.strip() + " " +
#                     ingredient.select_one('div.ingredient-unit').text.strip()
#                     for ingredient in ingredients_Obj
#                 ]

#                 # 食譜作法
#                 recipe_details_Obj = content_soup.select('ul[class="recipe-details-steps"]')
#                 detail_content = ''
#                 for detail in recipe_details_Obj:
#                     details = detail.select('p[class="recipe-step-description-content"]')
#                     detail_content += '\n'.join([step.text.strip() for step in details])
#                 recipe_ingredient["RecipeDetail"] = detail_content

#         except Exception as e:
#             print("Error extracting data:", e)
#             continue

#         # 確保每次食譜都有名稱和網址才儲存
#         if "RecipeName" in recipe_ingredient and "Url" in recipe_ingredient:
#             all_recipes.append(recipe_ingredient)

#     print(f"----- Page {page:^6} complete! -----")
#     page += 1

# # 將所有食譜儲存到 JSON 檔案中
# output_path = './icook/recipe.json'
# with open(output_path, 'w', encoding='utf-8') as j:
#     json.dump(all_recipes, j, ensure_ascii=False, indent=4)
#     print("Writing complete! File saved as:", output_path)

