import requests
from bs4 import BeautifulSoup
import re
import json
import os

def fetch_recipes(ingredients):
    base_url = "https://icook.tw/recipes/search?q={}&page={}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    all_recipes = []

    for ingredient in ingredients:
        for page in range(1, 2):  # 假設只爬取每個食材的前一頁
            try:
                res = requests.get(url=base_url.format(ingredient, page), headers=headers, timeout=10)
                res.raise_for_status()  # 檢查請求是否成功
            except requests.RequestException as e:
                print(f"Error fetching page {page} for ingredient {ingredient}: {e}")
                continue

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

                    all_recipes.append(recipe_data)
                except Exception as e:
                    print(f"Error processing recipe: {e}")
                    continue

    # 儲存到 JSON 檔案
    output_path = os.path.join(os.path.dirname(__file__), 'recipe.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_recipes, f, ensure_ascii=False, indent=4)

    return all_recipes

# 測試函數
if __name__ == "__main__":
    ingredients = ["泡菜"]
    recipes = fetch_recipes(ingredients)