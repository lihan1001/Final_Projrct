//nevigation.js
// 切換頁面功能
const fridgePage = document.getElementById('fridge');
const recipesPage = document.getElementById('recipes');

document.getElementById('nav-fridge').onclick = () => {
    showPage(fridgePage);
};

// document.getElementById('nav-recipes').onclick = () => { //點擊頁面顯示程式端爬取的資料(舊)
//     showPage(recipesPage);
// };

document.getElementById('nav-recipes').onclick = async () => { //點擊頁面觸發爬蟲(新)
    await fetchRecipesFromFridge();
    showPage(recipesPage);
};

function showPage(page) {
    fridgePage.classList.add('hidden');
    recipesPage.classList.add('hidden');
    page.classList.remove('hidden');
}
//----------------------------------------------------
//modal.js
// 彈出框功能
// 獲取按鈕和彈出框元素
const showBoxButton = document.getElementById('showBoxButton');
const popupBox = document.getElementById('popupBox');
const closeButton = document.getElementById('closeButton');

// 顯示彈出框
showBoxButton.addEventListener('click', () => {
    popupBox.style.display = 'block';
});

// 關閉彈出框
closeButton.addEventListener('click', () => {
    popupBox.style.display = 'none';
});
//------------------------------------------------------
//food.js
// 編輯冰箱內食材
// 用来保存每个分类的显示状态
const categoryVisibility = {};

// 加载食材并保留分类状态，同时添加过期提醒
function loadFood() {
    const displayDiv = document.getElementById('ingredient-table');
    const warningDiv = document.querySelector('.warning');
    displayDiv.innerHTML = ''; // 清空旧内容
    warningDiv.innerHTML = ''; // 清空警告信息

    // 用来分类食材的容器
    const categories = {
        '豆類/蛋/肉': [],
        '蔬果': [],
        '冷凍': []
    };

    // 从 Local Storage 获取数据并按类别分类
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        
        if (key.startsWith('food-')) {
            const food = JSON.parse(localStorage.getItem(key));
            
            if (food && food.category) {
                // 确保类别数组存在
                if (!categories[food.category]) {
                    categories[food.category] = [];
                }
                // 将食材添加至对应分类
                categories[food.category].push(food);
            } else {
                console.warn(`無效的 food 資料:`, food);
            }
        }
        // if (key.startsWith('food-')) {
        //     const food = JSON.parse(localStorage.getItem(key));
        //     categories[food.category].push(food); // 根据分类将食材加入相应的类别数组
        // }
    }

    // 统计即将过期的食材数量
    const expiryWarning = {
        '豆類/蛋/肉': 0,
        '蔬果': 0,
        '冷凍': 0
    };

    // 统计已經过期的食材数量
    const alreadyexpiryWarning = {
        '豆類/蛋/肉': 0,
        '蔬果': 0,
        '冷凍': 0
    };

    const currentDate = new Date();

    // 创建分类区域
    Object.keys(categories).forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.classList.add('category-section');
        
        const categoryHeader = document.createElement('h3');
        categoryHeader.textContent = category;
        categoryDiv.appendChild(categoryHeader);
        
        const table = document.createElement('table');
        const isVisible = categoryVisibility[category] || false; // 默认折叠
        table.style.display = isVisible ? 'table' : 'none'; // 根据状态设置显示状态

        const headerRow = document.createElement('tr');
        headerRow.innerHTML = `
            <th>名稱</th>
            <th>數量</th>
            <th>有效期限</th>
            <th>分類</th>
            <th></th>
        `;
        table.appendChild(headerRow);
        
        // 将该分类下的食材渲染到表格中
        categories[category].forEach(food => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${food.name}</td>
                <td>${food.quantity}</td>
                <td>${food.expiry}</td>
                <td>${food.category}</td>
            `;
            // 检查是否即将过期
            const foodExpiry = new Date(food.expiry);
            const timeDiff = foodExpiry - currentDate;
            const daysUntilExpiry = Math.ceil(timeDiff / (1000 * 60 * 60 * 24)); // 转换为天数

            if (daysUntilExpiry > 0 && daysUntilExpiry <= 7) {
                row.classList.add('warning-row'); // 给即将过期的食材添加警告样式
                expiryWarning[category]++; // 增加对应分类的过期提醒计数
            }

            // 添加删除按钮
            const actionCell = document.createElement('td');
            const deleteButton = document.createElement('button');
            deleteButton.textContent = '刪除';
            const foodKey = `food-${food.name}`; // 确保使用正确的键名
            deleteButton.onclick = () => deleteIngredient(foodKey);

            actionCell.appendChild(deleteButton);
            row.appendChild(actionCell);
            table.appendChild(row);
        });

        categoryDiv.appendChild(table);
        displayDiv.appendChild(categoryDiv);

        // 添加点击事件以切换显示/隐藏
        categoryHeader.addEventListener('click', () => {
            const currentState = table.style.display === 'none';
            table.style.display = currentState ? 'table' : 'none'; // 切换状态
            categoryVisibility[category] = currentState; // 更新状态记录
        });
    });

    // 显示过期提醒
    Object.keys(expiryWarning).forEach(category => {
        if (expiryWarning[category] > 0) {
            const warningMessage = document.createElement('p');
            warningMessage.textContent = `${category} 分類中有 ${expiryWarning[category]} 個食材即將過期！`;
            warningDiv.appendChild(warningMessage);
        }
    });

    Object.keys(alreadyexpiryWarning).forEach(category => {
        if (alreadyexpiryWarning[category] > 0) {
            const warningMessage = document.createElement('p');
            warningMessage.textContent = `${category} 分類中有 ${alreadyexpiryWarning[category]} 個食材已經過期！`;
            warningDiv.appendChild(warningMessage);
        }
    });  
}

// 添加食材到 Local Storage
function addIngredient() {
    const name = document.getElementById("name").value.trim();
    const quantity = document.getElementById("quantity").value.trim();
    const expiry = document.getElementById("expiry").value.trim();
    const category = document.getElementById("category").value;
    const popupBox = document.getElementById('popupBox');

    if (name && quantity && expiry) {
        const key = `food-${name}`;
        if (localStorage.getItem(key)) {
            alert("該食材已存在，請修改名稱！");
            return;
        }
        const food = {name, quantity, expiry, category};
        localStorage.setItem(key, JSON.stringify(food));
        alert(`已添加：\n名稱：${name}\n數量：${quantity}\n有效期限：${expiry}\n分類：${category}`);
        
        // 清空輸入框內容
        document.getElementById("name").value = '';
        document.getElementById("quantity").value = '';
        document.getElementById("expiry").value = '';
        document.getElementById("category").value = '';

        loadFood();
        popupBox.style.display = 'none'; // 添加完成後關閉懸浮窗
    } else {
        alert("請填寫所有必填項目！");
    }

    // 打包成一個JSON
    const data = {
        name: name,
        quantity: quantity,
        expiry: expiry,
        category: category
    };

    // 發送 POST 請求到 Node.js 後端
    fetch('https://final-projrct.onrender.com/save_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data) // 將資料轉成 JSON 格式
    })
    .then(response => response.json())
    .then(result => {
        alert(result.message); // 後端回應的消息
    })
    .catch(error => console.error('錯誤:', error));
}

// 刪除對應的食材並更新表格
function deleteIngredient(key) {
    const food = JSON.parse(localStorage.getItem(key));
    if (confirm(`確定要刪除「${food.name}」嗎？`)) {
        localStorage.removeItem(key); // 从 localStorage 删除
        loadFood(); // 更新表格
    }
}

function deleteIngredient(key) {
    const foodData = localStorage.getItem(key);

    if (!foodData) {
        alert('找不到該資料，可能已被刪除。');
        return;
    }

    try {
        const food = JSON.parse(foodData);
        if (!food || !food.name) throw new Error('資料格式錯誤');

        if (confirm(`確定要刪除「${food.name}」嗎？`)) {
            localStorage.removeItem(key);
            loadFood(); // 更新畫面
        }
    } catch (e) {
        alert('刪除失敗：資料格式不正確。');
        console.error(e);
    }
}

//--------------------------------------------------------
//recipes.js //功能和fetchRecipes重複
// function loadRecipes() {
//     const recipeList = document.getElementById('recipe-list');

//     // 假設你的 JSON 文件路徑統一在 "./icook/" 目錄
    
//     //fetch('./icook/recipe.json')// JSON 文件可以合併為一個或多個
//     fetch('http://localhost:8000/icook/recipe.json')
//         .then(response => response.json())
//         .then(data => {
//             recipeList.innerHTML = ''; // 清空列表

//             data.forEach(recipe => {
//                 // 創建食譜卡片
//                 const recipeItem = document.createElement('li');
//                 recipeItem.className = 'recipe-card';

//                 recipeItem.innerHTML = `
//                     <h3>${recipe.RecipeName}</h3>
//                     <a href="${recipe.Url}" target="_blank">
//                         <img src="${recipe.Image}" alt="${recipe.RecipeName}">
//                     </a>
//                     <p>${recipe.RecipeDetail}</p>
//                     <ul>
//                         ${recipe.Ingredients.map(ing => `<li>${ing.name}: ${ing.quantity}</li>`).join('')}
//                     </ul>
//                 `;
//                 recipeList.appendChild(recipeItem);
//             });
//         })
//         .catch(err => console.error('載入食譜失敗', err));
// }
//---------------------------------------------------------
//main.js
window.onload = function () { // 頁面載入時執行
    loadFood();  // 載入食材
    //fetchRecipes(); // 載入食譜
    fetchRecipesFromFridge();
    //loadRecipes(); // 載入食譜
};
//---------------------------------------------------------
//recipes.js
//fetchRecipes : 從一個固定的 JSON 檔案（recipe.json）中讀取食譜，並顯示到網頁。
async function fetchRecipes() {
    try {
        const response = await fetch('https://final-projrct.onrender.com/icook/recipe.json'); // 從本地後端伺服器獲取資料
        const recipes = await response.json();

        const container = document.getElementById('recipes-container');
        container.innerHTML = ''; // 清空容器內容

        recipes.forEach(recipe => {
            const recipeDiv = document.createElement('div');
            recipeDiv.classList.add('recipe');

            recipeDiv.innerHTML = `
                <div class="recipe-text">
                    <h2>${recipe.RecipeName}</h2>
                    <p><strong>網址：</strong> <a href="${recipe.Url}" target="_blank">${recipe.Url}</a></p>
                    <p><strong>食材：</strong> ${recipe.Ingredients.join(', ')}</p>
                    <p><strong>作法：</strong><br>${recipe.RecipeDetail.replace(/\n/g, '<br>')}</p>
                    <img src="${recipe.Image || 'placeholder.jpg'}" alt="食譜圖片">
                </div>
            `;

            container.appendChild(recipeDiv);
        });
    } catch (error) {
        console.error('Error fetching recipes:', error);
    }
}
// fetchRecipesFromFridge : 動態地根據冰箱內的食材（localStorage）向後端發送請求，爬取與食材匹配的食譜，並更新到網頁。
async function fetchRecipesFromFridge() {
    try {
         // 從 LocalStorage 收集食材清單
        const ingredients = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith("food-")) {
                const food = JSON.parse(localStorage.getItem(key));
                ingredients.push(food.name);
            }
        }

        if (ingredients.length === 0) {
            alert("冰箱中無食材！");
            return;
        }

         // 傳送食材清單到後端以觸發爬蟲
         // 發送包含食材的 POST 請求到 Node.js(8001) /fetch_recipes 路由
        const response = await fetch('https://final-projrct.onrender.com/fetch_recipes', { // 注意端口為 8001
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ingredients })
        });

        const result = await response.json();


        if (response.ok) {
            alert(`成功爬取 ${result.recipe_count} 筆食譜！`);
            fetchRecipes(); // 更新食譜顯示
        } else {
            console.error("Error fetching recipes:", result.error);
            alert("爬取食譜時發生錯誤！");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("無法連接到後端服務！");
    }
}
