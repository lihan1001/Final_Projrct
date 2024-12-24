//建立後端 Node.js 伺服器
const express = require('express'); //將內建express模駔引入，
const fs = require('fs'); // 
const path = require('path'); // 
const cors = require('cors');
const bodyParser = require('body-parser');
const { exec } = require('child_process'); // 引入 exec 來執行外部命令

// 啟用 CORS 和 bodyParser
const app = express(); //
const port = 8000;

// Middleware
app.use(cors());
app.use(bodyParser.json()); // 解析 JSON 格式的請求體

// 獲取 recipe.json 的內容
app.get('/recipes', (req, res) => {
    const filePath = path.join(__dirname, 'recipe.json');

    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            console.error('Error reading recipe.json:', err);
            return res.status(500).json({ error: 'Internal Server Error' });
        }
        res.json(JSON.parse(data)); // 回傳 JSON 格式
    });
});

// 根據食材進行爬蟲，回傳對應的食譜
app.post('/fetch_recipes', async (req, res) => { //async:非同步
    const { ingredients } = req.body;

    if (!ingredients || !Array.isArray(ingredients) || ingredients.length === 0) {
        return res.status(400).json({ error: 'No ingredients provided or invalid format' });
    }

    try {
        // 發送 POST 請求到 Python 爬蟲服務
        const response = await axios.post('https://final-projrct-recipe.onrender.com/fetch_recipes', { ingredients });

        // 獲取爬蟲結果
        const recipes = response.data;

        // 將結果寫入 recipe.json
        const filePath = path.join(__dirname, 'recipe.json');
        fs.writeFile(filePath, JSON.stringify(recipes, null, 2), (err) => {
            if (err) {
                console.error('Error writing to recipe.json:', err);
                return res.status(500).json({ error: 'Failed to save recipes' });
            }
            res.json({ message: 'Recipes fetched successfully', recipe_count: recipes.length, recipes });
        });
    } catch (error) {
        console.error('Error calling Python scraper:', error);
        res.status(500).json({ error: 'Failed to fetch recipes' });
    }
});

// 接收前端發送的多屬性資料
app.post('/save_data', (req, res) => {
    const data = req.body; // 解析 JSON 資料
    console.log("接收到的資料:", data);

    // 將資料保存到檔案中（覆蓋舊資料）
    fs.writeFile("../dict/fridge_data.json", JSON.stringify([data], null, 2), (writeErr) => {
        if (writeErr) {
            console.error("寫入檔案時發生錯誤:", writeErr);
            res.status(500).send({ message: '寫入檔案失敗' });
        }

        // 新資料已成功寫入，觸發 Python 腳本
        exec('python ../dict/quickstart.py', (err, stdout, stderr) => {
            if (err) {
                console.error(`exec error: ${err}`);
                return;
            }
            console.log(`Python 腳本輸出: ${stdout}`);
            if (stderr) {
                console.error(`stderr: ${stderr}`);
            }
        });
    });
});


app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});
