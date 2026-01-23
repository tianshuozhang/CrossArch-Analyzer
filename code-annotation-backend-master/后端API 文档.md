# 前端调用逻辑说明

（下面是前端的调用逻辑说明具体的接口说明见下）

登录页面
- 用户输入用户名、密码、确认密码，点击注册按钮，调用 `User/register` 接口注册用户
- 用户输入用户名和密码，点击登录按钮，调用 `User/login` 接口登录系统

开始页面
- 用户点击上传按钮，调用 `Project/upload` 接口上传项目文件，得到项目的目录树，然后从目录树中选择要打开的文件，调用 `File/open` 接口获取文件的内容，进入打开项目页面（这里用页面方便说明，实际可以共用一个页面）

管理项目页面
- 用户可以管理自己的项目：首先打开管理页面，调用`Project/get_project_list`接口获取项目列表，用户可以选择要管理的项目
  - 点击删除按钮，调用`Project/delete`接口删除项目
  - 点击添加按钮，调用`Project/add`接口添加项目
  - 点击打开按钮，调用`Project/open`接口打开项目
  - 点击展开按钮，调用`Project/get_tree`接口获取项目目录树
  - 点击分析按钮，调用`Analysis/analysis`接口启动项目架构分析，分析完成后，前端需要轮询调用`Analysis/progress`接口获取分析状态，直到分析完成。当分析完成后，调用`Analysis/fetch`接口获取分析结果（但由于是管理页面，所以这个分析结果不会显示，这里只报告给用户分析完成即可，用户之后可以点击下载报告按钮下载报告，或者打开项目进行浏览）
  - 点击下载报告按钮，调用`Analysis/report`接口下载项目分析报告

打开项目页面
- 点击关闭项目按钮，调用`Project/close`接口关闭项目
- 在目录树中点击要打开的文件，调用`File/open`接口获取文件的内容，进入打开文件页面
- 点击加载可视化图按钮，调用`Graph/get_list`接口获取可视化图下拉列表，用户可以选择要加载的可视化图，然后调用`Graph/get_graph`接口获取可视化图的内容，加载到页面上
- 点击下载按钮，调用`Analysis/report`接口下载项目分析报告
- 用户输入聊天内容，点击提交按钮，调用`Analysis/ask`接口获取项目架构分析结果，包括回答和可视化图（可选）
- 点击分析按钮，启动项目架构分析，调用`Analysis/analysis`接口。当启动分析后，前端需要轮询调用`Analysis/progress`接口获取分析状态，直到分析完成。当分析完成后，调用`Analysis/fetch`接口获取分析结果。
- 点击取消按钮，调用`Analysis/cancel`接口取消项目架构分析

打开文件页面
- 点击保存按钮，调用`File/save`接口保存文件内容
- 点击撤销按钮，调用`File/cancel`接口撤销最近一次文件内容的修改
- 点击关闭文件按钮，调用`File/close`接口关闭文件
- 点击行的标签进行修改，调用`ArchTag/modify`接口修改标签内容和颜色

---

# 用户模块 API 文档

## 基础信息

|项|值|
|---|---|
|基础路径|/User|
|数据格式|请求：form-data / 响应：JSON|
|认证方式|修改密码接口需 JWT Token 认证|
---

## 1. 用户登录接口

### 接口信息

- **接口路径**：`/login`

- **请求方法**：POST

- **接口描述**：用户登录并获取 JWT 令牌，登录成功后会初始化用户目录和默认标签

### 请求参数（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|username|string|是|用户名|
|password|string|是|用户密码（明文）|
### 响应示例

#### 成功响应（200 OK）

```JSON

{
  "state": "success",
  "description": "登录成功",
  "rst": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user_id": 1001,
    "username": "test_user"
  }
}
```

#### 失败响应（400 Bad Request）

```JSON

{
  "state": "fail",
  "description": "用户名或密码错误",
  "rst": {}
}
```

### 状态码说明

|状态码|说明|
|---|---|
|200|登录成功|
|400|用户名或密码错误|
---

## 2. 用户注册接口

### 接口信息

- **接口路径**：`/register`

- **请求方法**：POST

- **接口描述**：用户注册，包含参数校验、密码哈希存储，注册成功返回用户基础信息

### 请求参数（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|username|string|是|用户名（3-50个字符）|
|password|string|是|密码（至少6个字符）|
### 响应示例

#### 成功响应（201 Created）

```JSON

{
  "state": "success",
  "description": "登录成功",
  "rst": {
    "username": "test_user",
    "user_id": 1001
  }
}
```

#### 失败响应示例

1. 用户名已存在（400 Bad Request）

```JSON

{
  "state": "fail",
  "description": "用户名已存在",
  "rst": {}
}
```

1. 密码长度不足（400 Bad Request）

```JSON

{
  "state": "fail",
  "description": "密码长度至少6个字符",
  "rst": {}
}
```

1. 服务器异常（500 Internal Server Error）

```JSON

{
  "state": "fail",
  "description": "后端注册用户失败",
  "rst": {}
}
```

### 状态码说明

|状态码|说明|
|---|---|
|201|注册成功|
|400|参数错误/用户名已存在/用户名/密码格式不合法|
|500|服务器内部错误|
---

## 3. 修改密码接口

### 接口信息

- **接口路径**：`/modify_password`

- **请求方法**：POST

- **接口描述**：已登录用户修改密码，需携带有效的 JWT Token 认证

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数

#### 请求头

|参数名|类型|是否必传|说明|
|---|---|---|---|
|Authorization|string|是|Bearer + 空格 + JWT Token|
#### 请求体（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|old_password|string|是|用户当前密码（明文）|
|new_password|string|是|新密码（至少6个字符）|
### 响应示例

#### 成功响应（200 OK）

```JSON

{
  "state": "success",
  "description": "密码修改成功",
  "rst": {}
}
```

#### 失败响应示例

1. 旧密码错误（400 Bad Request）

```JSON

{
  "state": "fail",
  "description": "旧密码错误",
  "rst": {}
}
```

1. 新密码与旧密码相同（400 Bad Request）

```JSON

{
  "state": "fail",
  "description": "新密码不能与旧密码相同",
  "rst": {}
}
```

1. 用户不存在（404 Not Found）

```JSON

{
  "state": "fail",
  "description": "用户不存在",
  "rst": {}
}
```

1. 数据库更新失败（500 Internal Server Error）

```JSON

{
  "state": "fail",
  "description": "后端数据库里密码修改失败",
  "rst": {}
}
```

### 状态码说明

|状态码|说明|
|---|---|
|200|密码修改成功|
|400|参数错误/旧密码错误/新密码格式不合法/新密码与旧密码相同|
|404|用户不存在|
|500|数据库更新密码失败|
---

# 项目模块 API 文档

## 基础信息

|项|值|
|---|---|
|基础路径|/Project|
|数据格式|请求：form-data（文件上传）/ GET参数（部分接口）；响应：JSON|
|认证方式|所有接口均需 JWT Token 认证，请求头携带 Authorization: Bearer <token>|
|核心依赖|文件处理（zip压缩/解压、目录操作）、数据库交互（项目/文件/用户）、Token校验|
## 接口详情

### 1. 上传项目接口

#### 接口信息

- 接口路径：`/upload`

- 请求方法：POST

- 接口描述：上传项目文件（支持单个文件或zip压缩包），自动注册项目信息、保存文件、生成目录树，并自动打开该项目

- 核心逻辑：文件校验 → 项目注册与保存（zip格式处理）→ 文件信息注册 → 目录树生成 → 自动打开项目

#### 请求参数

##### 请求头

|参数名|类型|是否必传|说明|
|---|---|---|---|
|Authorization|string|是|Bearer + 空格 + JWT Token（登录接口获取）|
##### 请求体（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|file|FileStorage|是|项目文件（支持单个文件或zip压缩包），需包含有效文件名|
#### 响应示例

##### 成功响应（201 Created）

```json

{
  "state": "success",
  "description": "成功上传项目",
  "rst": {
    "project_id": 1001,
    "project_name": "test_project",
    "file_tree": {
      "name": "test_project",
      "type": "dir",
      "children": [
        {
          "name": "test.txt",
          "type": "file"
        }
      ]
    }
  }
}
```

##### 失败响应

1. 未上传文件（400 Bad Request）

```json

{
  "state": "fail",
  "description": "请上传文件",
  "rst": {}
}
```

2. 无文件名（400 Bad Request）

```json

{
  "state": "fail",
  "description": "请上传有文件名的文件",
  "rst": {}
}
```

3. 文件名无效（400 Bad Request）

```json

{
  "state": "fail",
  "description": "文件名无效",
  "rst": {}
}
```

4. 项目打开失败（500 Internal Server Error）

```json

{
  "state": "fail",
  "description": "上传项目时打开项目失败",
  "rst": {
    "msg": "打开项目失败：xxx（具体错误信息）"
  }
}
```

#### 状态码说明

|状态码|说明|
|---|---|
|201|项目上传成功，并已自动打开|
|400|参数错误（未上传文件、无文件名、文件名无效）|
|500|服务器内部错误（项目打开失败等）|
### 2. 添加项目接口

#### 接口信息

- 接口路径：`/add`

- 请求方法：POST

- 接口描述：上传项目文件并注册项目信息（功能与/upload类似，但添加后不自动打开项目）

- 核心逻辑：与/upload一致，仅省略“自动打开项目”步骤

#### 请求参数

与【上传项目接口】完全一致（请求头、请求体均相同）

#### 响应示例

##### 成功响应（201 Created）

```json

{
  "state": "success",
  "description": "成功添加项目",
  "rst": {
    "project_id": 1002,
    "project_name": "new_project"
  }
}
```

##### 失败响应

与【上传项目接口】的失败响应完全一致（400/500状态码及响应格式相同）

#### 状态码说明

与【上传项目接口】完全一致，201表示项目添加成功（未打开）

### 3. 获取项目列表接口

#### 接口信息

- 接口路径：`/get_project_list`

- 请求方法：POST

- 接口描述：根据当前登录用户ID，查询该用户名下的所有项目列表，返回项目ID、名称、修改时间

#### 请求参数

##### 请求头

与前文一致（Authorization: Bearer <token>）

##### 请求体

无额外参数（仅需Token认证，通过Token解析用户ID）

#### 响应示例

##### 成功响应（200 OK）

```json

{
  "state": "success",
  "description": "成功获取项目列表",
  "rst": {
    "list": [
      {
        "id": 1001,
        "name": "test_project",
        "modified_time": "2026-01-20 10:30:00"
      },
      {
        "id": 1002,
        "name": "new_project",
        "modified_time": "2026-01-20 11:15:00"
      }
    ]
  }
}
```

#### 状态码说明

|状态码|说明|
|---|---|
|200|项目列表获取成功（即使无项目，list返回空数组）|
|401|Token认证失败（过期、无效）|
### 4. 打开项目接口

#### 接口信息

- 接口路径：`/open`

- 请求方法：POST

- 接口描述：根据项目ID打开指定项目，打开成功后返回项目目录树

- 核心逻辑：项目ID校验 → 执行打开项目操作 → 读取项目目录树 → 返回结果

#### 请求参数

##### 请求头

与前文一致（Authorization: Bearer <token>）

##### 请求体（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|project_id|int|是|项目ID（需为有效整数，对应当前用户名下的项目）|
#### 响应示例

##### 成功响应（200 OK）

```json

{
  "state": "success",
  "description": "成功打开项目",
  "rst": {
    "project_id": 1001,
    "project_name": "test_project",
    "file_tree": {
      "name": "test_project",
      "type": "dir",
      "children": [
        {
          "name": "test.txt",
          "type": "file"
        }
      ]
    }
  }
}
```

##### 失败响应

1. 未提供项目ID（400 Bad Request）

```json

{
  "state": "fail",
  "description": "请提供项目ID",
  "rst": {}
}
```

2. 项目ID无效（非整数，400 Bad Request）

```json

{
  "state": "fail",
  "description": "项目ID无效",
  "rst": {}
}
```

3. 打开项目失败（500 Internal Server Error）

```json

{
  "state": "fail",
  "description": "打开项目失败",
  "rst": {
    "msg": "打开项目失败：xxx（具体错误信息）"
  }
}
```

#### 状态码说明

|状态码|说明|
|---|---|
|200|项目打开成功|
|400|参数错误（未提供项目ID、项目ID非整数）|
|500|服务器内部错误（打开项目操作失败）|
### 5. 关闭项目接口

#### 接口信息

- 接口路径：`/close`

- 请求方法：POST

- 接口描述：关闭当前用户正在打开的项目（无需指定项目ID，自动获取当前打开项目）

#### 请求参数

##### 请求头

与前文一致（Authorization: Bearer <token>）

##### 请求体

无额外参数（自动通过用户ID查询当前打开的项目）

#### 响应示例

##### 成功响应（200 OK）

```json

{
  "state": "success",
  "description": "关闭项目成功",
  "rst": {}
}
```

##### 失败响应

无打开的项目（400 Bad Request）

```json

{
  "state": "fail",
  "description": "没有打开的项目",
  "rst": {}
}
```

#### 状态码说明

|状态码|说明|
|---|---|
|200|当前打开的项目关闭成功|
|400|用户当前没有正在打开的项目|
### 6. 获取项目目录树接口

#### 接口信息

- 接口路径：`/get_tree`

- 请求方法：GET

- 接口描述：根据项目ID，读取项目压缩包内的目录树文件（tree.json），返回项目目录树

- 核心逻辑：获取项目ID → 定位项目压缩包 → 读取tree.json → 解析并返回目录树

#### 请求参数

##### 请求头

与前文一致（Authorization: Bearer <token>）

##### 请求参数（GET）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|project_id|int|是|项目ID（需为有效整数，对应当前用户名下的项目，且项目压缩包内存在tree.json）|
#### 响应示例

##### 成功响应（200 OK）

```json

{
  "state": "success",
  "description": "成功获取项目目录树",
  "rst": {
    "project_id": 1001,
    "project_name": "test_project",
    "file_tree": {
      "name": "test_project",
      "type": "dir",
      "children": [
        {
          "name": "test.txt",
          "type": "file"
        },
        {
          "name": "graph",
          "type": "dir",
          "children": []
        }
      ]
    }
  }
}
```

##### 失败响应

1. 未提供项目ID（400 Bad Request）：由GET参数校验触发，响应格式与前文失败响应一致

2. 项目压缩包不存在/无法读取（500 Internal Server Error）：响应格式与前文失败响应一致

#### 状态码说明

|状态码|说明|
|---|---|
|200|项目目录树获取成功|
|400|参数错误（未提供项目ID、项目ID无效）|
|500|服务器内部错误（项目压缩包不存在、无法读取tree.json等）|
### 7. 删除项目接口

#### 接口信息

- 接口路径：`/delete`

- 请求方法：POST

- 接口描述：根据项目ID删除指定项目，若该项目为当前打开项目，会先自动关闭再删除

- 核心逻辑：项目ID校验 → 关闭当前打开的目标项目（若有）→ 数据库删除项目记录 → 删除本地项目压缩包

#### 请求参数

##### 请求头

与前文一致（Authorization: Bearer <token>）

##### 请求体（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|project_id|int|是|项目ID（需为有效整数，对应当前用户名下的项目）|
#### 响应示例

##### 成功响应（200 OK）

```json

{
  "state": "success",
  "description": "成功删除项目",
  "rst": {}
}
```

##### 失败响应

数据库删除失败（500 Internal Server Error）

```json

{
  "state": "fail",
  "description": "删除项目失败",
  "rst": {}
}
```

#### 状态码说明

|状态码|说明|
|---|---|
|200|项目删除成功（数据库记录+本地文件均删除）|
|400|参数错误（未提供项目ID、项目ID非整数）|
|500|服务器内部错误（数据库删除失败、本地文件删除失败等）|

---

# 文件模块 API 文档

文件模块接口依赖项目模块，需先打开项目后方可执行文件操作，核心实现文件的打开、保存、取消修改、关闭功能，同时管理文件临时版本和关联关系。

## 接口详情

### 1. 打开文件接口

#### 接口信息

- 接口路径：`/open`

- 请求方法：POST

- 接口描述：根据文件相对路径，读取文件内容及行级架构标签，返回给前端（需先打开对应项目）

- 核心逻辑：文件路径校验 → 调用工具函数读取文件数据及标签 → 返回结果

#### 请求参数

##### 请求头

|参数名|类型|是否必传|说明|
|---|---|---|---|
|Authorization|string|是|Bearer + 空格 + JWT Token（登录接口获取）|
##### 请求体（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|file_path|string|是|文件相对路径（对应打开项目内的文件路径，不可为空）|
#### 响应示例

##### 成功响应（200 OK）

```json


{
  "state": "success",
  "description": "成功",
  "rst": {
    "file_data":{
      "file_content": "print(\"Hello World\")\n# 测试注释",
      "tag_data":[
        {"start":1,"end":2,"arch_names":["arm","riscv"]},
        {"start":2,"end":2,"arch_names":["x86", "irrelevant"]}
      ]
    }
  }
}

```

##### 失败响应

1. 未提供文件路径（404 Not Found）

```json


{
  "state": "fail",
  "description": "没有提供文件路径",
  "rst": {}
}

```

2. 读取文件内容失败（200 OK，业务失败）

```json


{
  "state": "fail",
  "description": "读取文件内容失败",
  "rst": {}
}

```

#### 状态码说明

|状态码|说明|
|---|---|
|200|请求成功（含业务失败：读取文件内容失败）|
|404|未提供文件路径|
### 2. 保存文件接口

#### 接口信息

- 接口路径：`/save`

- 请求方法：POST

- 接口描述：保存文件内容及文件标签关联关系，生成临时文件版本，更新文件修改时间（需先打开对应项目）

- 核心逻辑：参数校验 → 删除旧关联关系 → 新增关联关系 → 生成临时文件 → 保存文件内容 → 更新修改时间

#### 请求参数

##### 请求头

与前文一致（Authorization: Bearer <token>）

##### 请求体（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|file_path|string|是|文件相对路径（对应打开项目内的文件路径，用于查询文件ID）|
|file_data|dict|是|要保存的文件数据，示例{"file_content":"print(\"Hello World\")\n# 测试注释","tag_data":[{"start":1,"end":2,"arch_names":["arm","riscv"]},{"start":2,"end":2,"arch_names":["x86", "irrelevant"]}]}|
#### 响应示例

##### 成功响应（200 OK）

```json


{
  "state": "success",
  "description": "成功",
  "rst": {}
}

```

##### 失败响应

1. 未提供文件路径（404 Not Found）

```json


{
  "state": "fail",
  "description": "没有提供文件路径",
  "rst": {}
}

```

2. 未找到对应文件（404 Not Found）

```json


{
  "state": "fail",
  "description": "没有找到该文件",
  "rst": {}
}

```

3. 未提供文件内容（404 Not Found）

```json


{
  "state": "fail",
  "description": "没有提供要保存文件内容",
  "rst": {}
}

```

4. 未提供文件标签（404 Not Found）

```json


{
  "state": "fail",
  "description": "没有提供文件标签，如果当前没有文件标签，那么应该提供一个空的",
  "rst": {}
}

```

5. 没有打开项目（404 Not Found）

```json


{
  "state": "fail",
  "description": "没有打开项目，请先打开项目",
  "rst": {}
}

```

#### 状态码说明

|状态码|说明|
|---|---|
|200|文件保存成功|
|404|参数缺失、文件不存在或未打开项目|
### 3. 取消文件修改接口

#### 接口信息

- 接口路径：`/cancel`

- 请求方法：POST

- 接口描述：取消对文件的修改，恢复到最近一次保存的临时文件版本，删除对应的临时文件并更新临时文件计数（需先打开对应项目）

- 核心逻辑：参数校验 → 校验已打开项目 → 查询文件ID → 获取临时文件路径 → 读取临时文件内容 → 删除临时文件 → 更新临时文件计数 → 恢复文件内容 → 返回结果

#### 请求参数

##### 请求头

与前文一致（Authorization: Bearer <token>）

##### 请求体（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|file_path|string|是|文件相对路径（对应打开项目内的文件路径，用于查询文件ID）|
#### 响应示例

##### 成功响应（200 OK）

```JSON

{
  "state": "success",
  "description": "成功",
  "rst": {
    "file_content": "print(\"Hello World\")\n# 测试注释"
  }
}
```

##### 失败响应

1. 未提供文件路径（404 Not Found）

```JSON

{
  "state": "fail",
  "description": "没有提供文件路径",
  "rst": {}
}
```

1. 没有打开项目（404 Not Found）

```JSON

{
  "state": "fail",
  "description": "用户没有打开项目",
  "rst": {}
}
```

1. 未找到对应文件（404 Not Found）

```JSON

{
  "state": "fail",
  "description": "没有找到该文件",
  "rst": {}
}
```

1. 未找到临时文件（404 Not Found）

```JSON

{
  "state": "fail",
  "description": "没有找到该文件对应的临时文件",
  "rst": {}
}
```

#### 状态码说明

|状态码|说明|
|---|---|
|200|文件修改取消成功，已恢复到临时文件版本|
|404|参数缺失、文件不存在、未打开项目或未找到临时文件|
---

### 4. 关闭文件接口

#### 接口信息

- 接口路径：`/close`

- 请求方法：POST

- 接口描述：关闭文件并保存最终修改内容，删除该文件对应的所有临时文件目录，清零临时文件计数（需先打开对应项目）

- 核心逻辑：参数校验 → 保存文件内容 → 查询文件ID → 删除临时文件目录 → 清零临时文件计数 → 返回结果

#### 请求参数

##### 请求头

与前文一致（Authorization: Bearer <token>）

##### 请求体（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|file_path|string|是|文件相对路径（对应打开项目内的文件路径，用于查询文件ID）|
|file_data|dict|是|要保存的最终文件数据，格式与/save接口的file_data参数一致|
#### 响应示例

##### 成功响应（200 OK）

```JSON

{
  "state": "success",
  "description": "成功",
  "rst": {}
}
```

##### 失败响应

1. 未提供文件路径（404 Not Found）

```JSON

{
  "state": "fail",
  "description": "没有提供文件路径",
  "rst": {}
}
```

1. 未提供文件内容（404 Not Found）

```JSON

{
  "state": "fail",
  "description": "没有提供要保存文件内容",
  "rst": {}
}
```

1. 保存文件内容失败（404 Not Found）

```JSON

{
  "state": "fail",
  "description": "保存文件内容失败",
  "rst": {}
}
```

1. 未找到对应文件（404 Not Found）

```JSON

{
  "state": "fail",
  "description": "没有找到该文件",
  "rst": {}
}
```

#### 状态码说明

|状态码|说明|
|---|---|
|200|文件关闭成功，已保存最终内容并清理临时文件|
|404|参数缺失、文件不存在或保存文件内容失败|

# 分析模块 API 文档

## 基础信息

|项|值|
|---|---|
|基础路径|/Analysis|
|数据格式|请求：form-data / 响应：JSON（/report 接口为文件流）|
|认证方式|所有接口均需 JWT Token 认证|
---

## 1. 取消任务接口

### 接口信息

- **接口路径**：`/cancel`

- **请求方法**：POST

- **接口描述**：取消指定ID的分析任务，会等待任务终止并清理相关资源

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数（URL 参数）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|task_id|int|是|需要取消的任务ID|
### 响应示例

#### 成功响应（200 OK）

```JSON

{
  "state": "success",
  "description": "成功取消",
  "rst": {}
}
```

#### 失败响应示例

1. 缺少任务ID（400 Bad Request）

```JSON

{
  "state": "failed",
  "description": "请提供任务ID",
  "rst": {}
}
```

1. 任务取消超时（400 Bad Request）

```JSON

{
  "state": "failed",
  "description": "超时",
  "rst": {}
}
```

### 状态码说明

|状态码|说明|
|---|---|
|200|请求处理完成|
|400|缺少任务ID参数或任务取消超时|
---

## 2. 获取任务进度接口

### 接口信息

- **接口路径**：`/progress`

- **请求方法**：GET

- **接口描述**：查询指定分析任务的执行进度

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数（URL 参数）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|task_id|int|是|需要查询的任务ID|
### 响应示例

#### 成功响应（200 OK）

```JSON

{
  "state": "success",
  "description": "success",
  "rst": {
    "progress": 80
  }
}
```

#### 失败响应（404 Not Found）

```JSON

{
  "state": "failed",
  "description": "任务不存在",
  "rst": {}
}
```

### 状态码说明

|状态码|说明|
|---|---|
|200|查询成功|
|404|指定的任务ID不存在|
---

## 3. 智能问答接口

### 接口信息

- **接口路径**：`/ask`

- **请求方法**：POST

- **接口描述**：基于当前打开的项目进行智能问答，支持生成可视化图表数据

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|question|string|是|用户的提问内容|
### 响应示例

#### 成功响应（200 OK）

```JSON

{
  "state": "success",
  "description": "success",
  "rst": {
    "answer": "这是关于项目架构的分析回答...",
    "graph": {
      "title": "架构依赖图",
      "option": {
        "xAxis": ["模块A", "模块B"],
        "yAxis": [10, 20]
      }
    }
  }
}
```
如果不是关于图的问题，那么graph字段的值为空对象{}

#### 失败响应示例

1. 缺少问题内容（400 Bad Request）

```JSON

{
  "state": "failed",
  "description": "请提供问题",
  "rst": {}
}
```

1. 未打开任何项目（400 Bad Request）

```JSON

{
  "state": "failed",
  "description": "请先打开一个项目",
  "rst": {}
}
```

### 状态码说明

|状态码|说明|
|---|---|
|200|问答成功|
|400|缺少问题参数/未打开任何项目|
---

## 4. 获取分析结果接口

### 接口信息

- **接口路径**：`/fetch`

- **请求方法**：POST

- **接口描述**：获取已完成分析任务的结果，清理任务资源并保存分析报告

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数

#### 请求体（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|file_path|string|是|当前打开的文件路径（无打开文件则传空字符串）|
|project_id|int|是|项目ID|
|task_id|int|是|已完成的分析任务ID|

### 响应示例

#### 成功响应（无打开文件）（200 OK）

```JSON

{
  "state": "success",
  "description": "success",
  "rst": {}
}
```

#### 成功响应（有打开文件）（200 OK）

```JSON

{
  "state": "success",
  "description": "success",
  "rst": {
    "file_data": {
      "file_content": "def hello():\n    print('world')",
      "tag_data": [
        {
          "start": 1,
          "end": 2,
          "arch_names": ["arm", "x86"]
        }
      ]
    }
  }
```

#### 失败响应示例

1. 缺少参数（400 Bad Request）

```JSON

{
  "state": "failed",
  "description": "请提供项目ID",
  "rst": {}
}
```

1. 任务未完成（400 Bad Request）

```JSON

{
  "state": "failed",
  "description": "任务未完成，请稍后再试",
  "rst": {}
}
```

1. 分析了不存在的文件（404 Not Found）

```JSON

{
  "state": "failed",
  "description": "分析了不存在的文件",
  "rst": {}
}
```

1. 文件未找到（404 Not Found）

```JSON

{
  "state": "failed",
  "description": "没有找到文件",
  "rst": {}
}
```

1. 项目状态异常（400 Bad Request）

```JSON

{
  "state": "failed",
  "description": "只有一个项目被打开时才需要提供一个非空的字符串",
  "rst": {}
}
```

### 状态码说明

|状态码|说明|
|---|---|
|200|获取分析结果成功|
|400|缺少参数/任务未完成/项目状态异常|
|404|分析的文件不存在/指定文件未找到|
---

## 5. 启动分析任务接口

### 接口信息

- **接口路径**：`/analysis`

- **请求方法**：POST

- **接口描述**：启动指定项目的代码分析任务，返回任务ID用于后续查询进度

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|project_id|int|是|需要分析的项目ID|
### 响应示例

#### 成功响应（200 OK）

```JSON

{
  "state": "success",
  "description": "success",
  "rst": {
    "task_id": 1001
  }
}
```

#### 失败响应（400 Bad Request）

```JSON

{
  "state": "failed",
  "description": "请提供项目ID",
  "rst": {}
}
```

### 状态码说明

|状态码|说明|
|---|---|
|200|分析任务启动成功|
|400|缺少项目ID参数|
---

## 6. 获取分析报告接口

### 接口信息

- **接口路径**：`/report`

- **请求方法**：POST

- **接口描述**：下载指定项目的分析报告文件（包含文字报告和架构标注报告）

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|project_id|int|是|需要获取报告的项目ID|
### 响应说明

#### 成功响应（200 OK）

- 响应类型：`application/octet-stream`

- 响应内容：名为 `report.txt` 的文件流，包含文字分析报告和架构标注结构化报告

#### 失败响应示例

1. 缺少项目ID（400 Bad Request）

```JSON

{
  "state": "failed",
  "description": "请提供项目ID",
  "rst": {}
}
```

1. 未找到项目报告（404 Not Found）

```JSON

{
  "state": "failed",
  "description": "没有找到项目报告",
  "rst": {}
}
```

### 状态码说明

|状态码|说明|
|---|---|
|200|报告文件返回成功|
|400|缺少项目ID参数|
|404|指定项目的分析报告不存在|
---

# 架构标签模块 API 文档

## 基础信息

|项|值|
|---|---|
|基础路径|/ArchTag|
|数据格式|请求：form-data / 响应：JSON|
|认证方式|接口需 JWT Token 认证|
---

## 1. 修改架构标签接口

### 接口信息

- **接口路径**：`/modify`

- **请求方法**：POST

- **接口描述**：修改当前打开文件指定行的架构标签，支持删除原有标签、替换为新标签（含标签颜色设置），同步更新标签属性及文件行绑定关系，最终返回当前行的关系范围

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|file_path|string|是|当前打开文件的路径|
|line|int|是|需要修改标签的行位置（需传递数字格式，接口内部会进行类型转换）|
|remove_tag_text|string|是|需要删除的标签名字；若无需删除任何标签，需传递空字符串|
|arch_tag_text|string|是|需要修改成的新标签名字|
|arch_tag_color|string|是|需要修改成的新标签颜色|
### 响应示例

#### 成功响应（200 OK）

```JSON


{
  "state": "success",
  "description": "修改标签成功",
  "rst": {
    "start": 5,
    "end": 8
  }
}

```

用户修改了一行的标签，这里会返回当前行的关系范围（start/end），需要前端同步地把行所在的整个范围的标签都修改

#### 失败响应示例

1. 缺少文件路径参数（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "需要提供当前打开文件路径",
  "rst": {}
}

```

2. 缺少行位置参数（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "需要提供当前行位置",
  "rst": {}
}

```

3. 缺少需删除的标签名参数（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "需要提供要删除的标签名字，如果没有删除，那么需要提供一个空的字符串",
  "rst": {}
}

```

4. 缺少新标签名字参数（400 Bad Request）

```JSON

{
  "state": "fail",
  "description": "需要提供要修改成的标签名字",
  "rst": {}
}

```

5. 缺少新标签颜色参数（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "需要提供要修改成的标签颜色",
  "rst": {}
}

```

6. 修改标签属性失败（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "修改标签属性失败",
  "rst": {}
}

```

7. 用户未打开任何项目（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "当前用户没有打开项目",
  "rst": {}
}

```

8. 指定文件不存在（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "当前文件不存在",
  "rst": {}
}

```

9. 修改旧标签值失败（400 Bad Request）

```JSON

{
  "state": "fail",
  "description": "修改旧标签值失败",
  "rst": {}
}

```

10. 修改新标签值失败（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "修改新标签值失败",
  "rst": {}
}

```

11. 当前行无绑定关系（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "当前行没有绑定关系",
  "rst": {}
}

```

### 状态码说明

|状态码|说明|
|---|---|
|200|标签修改成功，返回当前行的关系范围（start/end）|
|400|缺少必要参数/参数格式错误/修改标签属性失败/用户未打开项目/文件不存在/标签值修改失败/当前行无绑定关系|
---

# 图表模块 API 文档

## 基础信息

|项|值|
|---|---|
|基础路径|/Graph|
|数据格式|请求：form-data / 响应：JSON|
|认证方式|所有接口均需 JWT Token 认证|
---

## 1. 获取图表列表接口

### 接口信息

- **接口路径**：`/get_list`

- **请求方法**：POST

- **接口描述**：根据指定项目ID，查询该项目下所有可视化图表的ID及标题列表，用于展示项目内所有可用图表

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|project_id|int|是|项目ID（需传递数字格式，接口内部会进行类型转换）|
### 响应示例

#### 成功响应（200 OK）

```JSON


{
  "state": "success",
  "description": "成功",
  "rst": {
    "graphs": [
      {"id": 1, "title": "架构依赖图"},
      {"id": 2, "title": "模块调用流程图"}
    ]
  }
}

```

#### 失败响应（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "没有提供项目ID",
  "rst": {}
}

```

### 状态码说明

|状态码|说明|
|---|---|
|200|图表列表查询成功，返回图表ID及标题列表|
|400|缺少项目ID参数|
---

## 2. 获取图表详情接口

### 接口信息

- **接口路径**：`/get_graph`

- **请求方法**：POST

- **接口描述**：根据指定图表ID，读取该图表的详细数据（从当前打开项目的压缩包中获取）并返回，用于图表渲染展示

- **认证要求**：请求头需携带 `Authorization: Bearer <token>`

### 请求参数（form-data）

|参数名|类型|是否必传|说明|
|---|---|---|---|
|graph_id|int|是|需要获取详情的图表ID|
### 响应示例

#### 成功响应（200 OK）

```JSON


{
  "state": "success",
  "description": "成功",
  "rst": {
    "option": {
      "xAxis": ["模块A", "模块B", "模块C"],
      "yAxis": [15, 25, 20],
      "series": [{"data": [15, 25, 20], "type": "bar"}]
    }
  }
}

```

#### 失败响应示例

1. 缺少图表ID参数（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "没有提供图ID",
  "rst": {}
}

```

2. 未打开任何项目（400 Bad Request）

```JSON


{
  "state": "fail",
  "description": "没有打开的项目",
  "rst": {}
}

```

### 状态码说明

|状态码|说明|
|---|---|
|200|图表详情获取成功，返回完整图表数据|
|400|缺少图表ID参数/用户未打开任何项目（无法定位图表文件所在压缩包）|
