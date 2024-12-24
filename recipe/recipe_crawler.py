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
            for page in range(1, 2):  # 假設只爬取每個食材的前一頁
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
                                # 選擇所有<li class="ingredient">元素
                            ingredients_obj = content_soup.select('li.ingredient')

                                # 提取食材名稱與數量，並存入recipe_data["Ingredients"]
                            recipe_data["Ingredients"] = [
                                f'{i.select_one("div.ingredient-name a").text.strip()} {i.select_one("div.ingredient-unit").text.strip()}'
                                for i in ingredients_obj
                            ]

                            # 作法
                            steps_obj = content_soup.select('ul.recipe-details-steps p.recipe-step-description-content')
                            recipe_data["RecipeDetail"] = "\n".join([step.text.strip() for step in steps_obj])

                            Image_tag = content_soup.select_one('div.recipe-cover img')
                            if Image_tag and 'src' in Image_tag.attrs:
                                recipe_data["Image"] = Image_tag["src"]
                                
                        if recipe_data.get("RecipeName") and recipe_data.get("Url"):
                            all_recipes.append(recipe_data)

                    except Exception as e:
                        print(f"Error processing recipe: {e}")
                        continue

        # 儲存到 JSON 檔案
        output_path = '../src/recipe.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_recipes, f, ensure_ascii=False, indent=4)

        return jsonify({"message": "Recipes fetched successfully", "recipe_count": len(all_recipes)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)  # 明確使用 0.0.0.0 支持所有網卡
