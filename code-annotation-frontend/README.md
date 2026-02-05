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
管理员：注册为
## 核心交互与后端

### 后端返回格式规范

前端定义了后端应返回的数据格式，特别是分析结果的annotations部分：

- `annotations`数组元素格式：
  - `line`: 行号（数字，从1开始）
  - `tags`: 标签数组（字符串数组，如["arm", "riscv"]）
  - `type`: 代码类型（字符串，如"function", "macro", "assembly"等）
  - `fn`: 函数名（字符串，可选）
  - `tagColor`: 标签背景颜色（十六进制颜色值，如"#dafbe1"，可选）
  - `customTag`: 自定义标签文本（字符串，可选）

- `codeContent`格式（可选）：
  - 完整代码内容，可以是字符串（按行分割）或对象数组（包含text、tags等字段）
  - 当后端需要更新前端显示的完整代码内容时使用此字段

前端会根据这些字段相应地更新代码显示、标签和颜色。

### 统计图表接口规范

前端为统计图表预留了接口，后端可以返回不同类型的统计图表数据：

- `POST /Analysis/statistics` 接口返回指定类型的统计图表数据：
  - `statType`参数：统计类型（"architecture"、"function"、"file"、"custom"）
  - 返回格式：
    ```json
    {
      "state": "success",
      "description": "获取统计图表数据成功",
      "rst": {
        "barData": [
          { "key": "标识", "label": "标签文本", "count": 数量, "percent": 百分比, "color": "颜色" }
        ]
      }
    }
    ```

- 图1：架构分布统计 - 显示ARM、RISC-V、通用代码的分布
- 图2：函数级别统计 - 显示按函数级别的架构分布
- 图3：文件级别统计 - 显示整个文件中各架构代码行数的分布



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
        "annotations": [ { "line": 12, "tags": ["riscv"], "type": "function", "fn": "calc_riscv", "tagColor": "#dafbe1", "customTag": "" } ],
        "report": "...文本报告...",
        "stats": { "funcCount": 3, "riscvFuncCount": 1, "fileArch": "riscv", "counts": { "arm": 0, "riscv": 10, "common": 5 } }
      }
    }
    ```
  - annotations格式说明：
    - `line`: 行号（数字，从1开始）
    - `tags`: 标签数组（字符串数组，如["arm", "riscv"]）
    - `type`: 代码类型（字符串，如"function", "macro", "assembly"等）
    - `fn`: 函数名（字符串，可选）
    - `tagColor`: 标签背景颜色（十六进制颜色值，如"#dafbe1"，可选）
    - `customTag`: 自定义标签文本（字符串，可选）
  - codeContent格式说明（可选）：
    - `codeContent`: 完整代码内容，可以是字符串（按行分割）或对象数组（包含text、tags等字段）
    - 当后端需要更新前端显示的完整代码内容时使用此字段

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
  - 参数：`username`, `password`
  - 成功示例：
    ```json
    { "state": "success", "description": "注册成功", "rst": { "username": "newuser" } }
    ```
  - 失败示例：
    ```json
    { "state": "fail", "description": "用户名已存在", "rst": null }
    ```
- `POST /User/login`
  - 参数：`username`, `password`
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
- `POST /User/modifyPassword`
  - 参数：`username`, `oldPassword`, `newPassword`
  - 成功示例：
    ```json
    { "state": "success", "description": "密码修改成功", "rst": { "username": "demo" } }
    ```
  - 失败示例：
    ```json
    { "state": "fail", "description": "原密码错误", "rst": null }
    ```
- `POST /User/removeUser`
  - 参数：`username`
  - 成功示例：
    ```json
    { "state": "success", "description": "用户删除成功", "rst": { "username": "demo" } }
    ```
  - 失败示例：
    ```json
    { "state": "fail", "description": "用户不存在", "rst": null }
    ```

## 管理
- `GET /Admin/getUsers`
  - 成功示例：
    ```json
    { "state": "success", "description": "获取用户列表成功", "rst": [{ "username": "user1", "telphone": "13800138000", "numFile": 5, "numTag": 10, "numRelation": 3 }] }
    ```
  - 失败示例：
    ```json
    { "state": "fail", "description": "获取用户列表失败", "rst": null }
    ```
- `POST /Admin/removeUser`
  - 参数：`userId`, `adminpassword`
  - 成功示例：
    ```json
    { "state": "success", "description": "用户删除成功", "rst": null }
    ```
  - 失败示例：
    ```json
    { "state": "fail", "description": "密码错误", "rst": null }
    ```
- `POST /Admin/removeUserProjects`
  - 参数：`userId`, `adminpassword`
  - 成功示例：
    ```json
    { "state": "success", "description": "用户项目删除成功", "rst": null }
    ```
  - 失败示例：
    ```json
    { "state": "fail", "description": "密码错误或用户不存在", "rst": null }
    ```
- `POST /Admin/removeProject`
  - 参数：`projectId`, `adminpassword`
  - 成功示例：
    ```json
    { "state": "success", "description": "项目删除成功", "rst": null }
    ```
  - 失败示例：
    ```json
    { "state": "fail", "description": "密码错误或项目不存在", "rst": null }
    ```

## 代码
- `GET|POST /Code/getCodes` 参数：`userId`
- `GET|POST /Code/getCode` 参数：`userId`, `codeId`
- `POST /Code/addCode` 参数：`userId`, `codeId`, `code`, `language`
- `POST /Code/removeCode` 参数：`userId`, `codeId`
- `POST /Code/modifyCodeID`
- `POST /Code/modifyCode`
- `POST /Code/report` 参数：`userId`, `codeId`（开发态从 `http://127.0.0.1:5000/Code/report` 调用）
- `POST /Analysis/analyze` 参数：`userId`, `codeId`, `code`, `language`, `prompt`（用于重新分析修改后的代码）
- `POST /Analysis/statistics` 参数：`userId`, `codeId`, `statType`（用于获取指定类型的统计图表数据）

## 项目管理
- `GET|POST /Project/list` 参数：`userId` - 获取用户项目列表
- `POST /Project/create` 参数：`userId`, `projectName` - 创建新项目
- `POST /Project/open` 参数：`userId`, `projectId` - 打开指定项目
- `POST /Project/delete` 参数：`userId`, `projectId` - 删除指定项目
- `POST /Project/rename` 参数：`userId`, `projectId`, `newName` - 重命名项目
- `POST /Project/upload` 参数：`userId`, `projectFile` - 上传项目文件
- `GET|POST /Project/tree` 参数：`userId`, `projectId` - 获取项目目录树
- `POST /Project/update` 参数：`userId`, `projectId`, `data` - 更新项目信息

## 状态管理
- `GET|POST /Status/get` 参数：`userId` - 获取当前系统状态
- `GET|POST /Status/upload` 参数：`userId` - 获取文件上传进度
- `GET|POST /Status/analysis` 参数：`userId` - 获取代码分析进度

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

## 项目管理接口示例响应

- `GET|POST /Project/list`
  - 请求体：`userId`
  - 成功示例：
    ```json
    { "state": "success", "description": "获取项目列表成功", "rst": [{ "id": 1, "name": "MyProject", "path": "/projects/myproject", "createTime": "2023-01-01 12:00:00" }] }
    ```

- `POST /Project/create`
  - 请求体：`userId`, `projectName`
  - 成功示例：
    ```json
    { "state": "success", "description": "项目创建成功", "rst": { "projectId": 1, "projectName": "MyProject" } }
    ```

- `POST /Project/open`
  - 请求体：`userId`, `projectId`
  - 成功示例：
    ```json
    { "state": "success", "description": "项目打开成功", "rst": { "projectId": 1, "projectName": "MyProject", "fileTree": [...] } }
    ```

- `POST /Project/delete`
  - 请求体：`userId`, `projectId`
  - 成功示例：
    ```json
    { "state": "success", "description": "项目删除成功", "rst": { "projectId": 1 } }
    ```

- `POST /Project/rename`
  - 请求体：`userId`, `projectId`, `newName`
  - 成功示例：
    ```json
    { "state": "success", "description": "项目重命名成功", "rst": { "projectId": 1, "newName": "NewProjectName" } }
    ```

- `POST /Project/upload`
  - 请求体：`userId`, `projectFile` (FormData)
  - 成功示例：
    ```json
    { "state": "success", "description": "项目上传成功", "rst": { "projectId": 1, "fileName": "myproject.zip", "size": 1024000 } }
    ```

- `GET|POST /Project/tree`
  - 请求体：`userId`, `projectId`
  - 成功示例：
    ```json
    { "state": "success", "description": "获取项目目录树成功", "rst": { "name": "MyProject", "type": "dir", "children": [...] } }
    ```

- `GET|POST /Status/get`
  - 请求体：`userId`
  - 成功示例：
    ```json
    { "state": "success", "description": "获取状态成功", "rst": { "isUploading": false, "isAnalyzing": true, "uploadProgress": 0, "analysisProgress": 65 } }
    ```

- `GET|POST /Status/upload`
  - 请求体：`userId`
  - 成功示例：
    ```json
    { "state": "success", "description": "获取上传进度成功", "rst": { "isUploading": true, "progress": 45 } }
    ```

- `GET|POST /Status/analysis`
  - 请求体：`userId`
  - 成功示例：
    ```json
    { "state": "success", "description": "获取分析进度成功", "rst": { "isAnalyzing": true, "progress": 78 } }
    ```

## 前端调用方式
- `GET`：`src/api/webget.js:getData(url, params)`
- `POST`：`src/api/webpost.js:postData(url, params)`
- 报告与上传在 `src/views/Preview.vue` 使用 `fetch` 调用 `/Code/*`

