## 启动与预览

- 依赖：Node.js ≥ 18
- 进入目录：`code-annotation-frontend`
- 安装依赖：`npm install`
- 开发预览：`npm run dev`
  - 终端会输出本地地址，例如 `http://localhost:5173/`（端口被占用会自动切换）
  - 访客进入首页：`http://localhost:5173/?guest=1`
  - 登录页：`http://localhost:5173/login`
- 构建产物：`npm run build`
- 预览构建：`npm run preview`（默认 `http://localhost:4173/`）
- 后端地址配置：
  - 默认 `apiBase = http://127.0.0.1:5000`
  - 可在浏览器控制台设置：`localStorage.setItem('apiBase', 'http://<host>:<port>')`

## 核心交互与后端

- 上传文件
  - 前端行为：读取本地文件，解析并在左侧文件树与代码预览展示
  - 后端交互：`POST /Analysis/analyze`
  - 触发位置：`src/views/Preview.vue:261–271`（上传完成后自动触发）
  - 请求体（FormData）：`userId`, `codeId`, `code`, `language`, `prompt`
  - 成功响应示例：
    ```json
    {
      "state": "success",
      "description": "分析完成",
      "rst": {
        "reply": "已根据需求完成分类",
        "annotations": [ { "line": 12, "tags": ["riscv"], "type": "function", "fn": "calc_riscv" } ],
        "report": "...文本报告...",
        "stats": { "funcCount": 3, "riscvFuncCount": 1, "fileArch": "riscv", "counts": { "arm": 0, "riscv": 10, "common": 5 } }
      }
    }
    ```

- 下载报告
  - 前端行为：优先请求后端生成报告，成功直接下载；失败走前端兜底生成文本
  - 后端交互：优先使用 `POST /Analysis/analyze` 返回的 `report`；若无则调用 `POST /Code/report`
  - 触发位置：`src/views/Preview.vue:291–318`
  - 请求体（FormData）：`userId`, `codeId`
  - 成功返回文件流（`application/octet-stream`）；失败返回 `{ state: "fail", description: "…" }`

- 分类结果统计
  - 前端行为：优先使用 `POST /Analysis/analyze` 返回的 `stats`；若无则本地计算
  - 位置：`src/views/Preview.vue:186–199`（`stats()`）、`src/views/Preview.vue:200–213`（`barData()`）

- 自然语言输入/输出
  - 前端行为：将输入作为 `prompt` 调用后端分析，展示后端 `reply`
  - 后端交互：`POST /Analysis/analyze`
  - 触发位置：`src/views/Preview.vue:350–360`（`send()`）

## 响应结构规范

- 统一返回字段：
  - `state`：`success` 或 `fail`
  - `description`：结果说明文本
  - `rst`：业务数据（对象或列表），失败时可为 `null`

示例：

```json
// 成功
{
  "state": "success",
  "description": "操作成功",
  "rst": { "username": "demo" }
}

// 失败
{
  "state": "fail",
  "description": "参数错误",
  "rst": null
}
```

前端错误处理参考：`src/api/index.js:38-69`（`axios` 失败时弹出 `HTTP CODE`）。

## 接口示例响应

- `POST /User/login`
  - 请求体：`telphone`, `password`
  - 成功示例：
    ```json
    { "state": "success", "description": "登录成功", "rst": { "username": "demo" } }
    ```
  - 失败示例：
    ```json
    { "state": "fail", "description": "账号或密码错误", "rst": null }
    ```

- `GET /User/exit`
  - 成功示例：
    ```json
    { "state": "success", "description": "退出成功", "rst": null }
    ```

- `POST /Code/addCode`
  - 请求体：`userId`, `codeId`, `code`, `language`
  - 成功示例：
    ```json
    { "state": "success", "description": "代码已保存", "rst": { "codeId": "driver.c" } }
    ```

- `POST /Code/removeCode`
  - 请求体：`userId`, `codeId`
  - 成功示例：
    ```json
    { "state": "success", "description": "代码已删除", "rst": { "codeId": "driver.c" } }
    ```

- `GET|POST /Code/getCodes`
  - 请求体：`userId`
  - 成功示例：
    ```json
    { "state": "success", "description": "", "rst": [ { "codeId": "driver.c" }, { "codeId": "global.h" } ] }
    ```

- `GET|POST /Code/getCode`
  - 请求体：`userId`, `codeId`
  - 成功示例：
    ```json
    { "state": "success", "description": "", "rst": { "codeId": "driver.c", "code": "int x=0;...", "language": "c" } }
    ```

- `POST /Code/report`
  - 请求体：`userId`, `codeId`
  - 成功：返回文件流（`Content-Type: application/octet-stream`），前端直接下载
  - 失败示例：
    ```json
    { "state": "fail", "description": "后端报告生成失败", "rst": null }
    ```

## 用户
- `POST /User/register`
- `POST /User/login` 参数：`telphone`, `password`
- `GET /User/exit`
- `POST /User/modifyPassword`
- `POST /User/removeUser`

## 管理
- `GET /Admin/getUsers`
- `POST /Admin/removeUser`

## 代码
- `GET|POST /Code/getCodes` 参数：`userId`
- `GET|POST /Code/getCode` 参数：`userId`, `codeId`
- `POST /Code/addCode` 参数：`userId`, `codeId`, `code`, `language`
- `POST /Code/removeCode` 参数：`userId`, `codeId`
- `POST /Code/modifyCodeID`
- `POST /Code/modifyCode`
- `POST /Code/report` 参数：`userId`, `codeId`（开发态从 `http://127.0.0.1:5000/Code/report` 调用）

## 标签与标注
- `GET|POST /Mark/getLabelMark`
- `GET|POST /Mark/getUserMark`
- `POST /Mark/addMark`
- `POST /Mark/removeMark`
- `GET|POST /Mark/getCodeMark`
- `GET|POST /UserLabel/getUser`
- `GET|POST /UserLabel/getLabel`
- `POST /UserLabel/addLabel`
- `POST /UserLabel/removeLabel`
- `POST /UserLabel/modifyLabelID`
- `POST /UserLabel/modifyLabelintro`

## 前端调用方式
- `GET`：`src/api/webget.js:getData(url, params)`
- `POST`：`src/api/webpost.js:postData(url, params)`
- 报告与上传在 `src/views/Preview.vue` 使用 `fetch` 调用 `/Code/*`

