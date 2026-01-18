<template>
  <div class="app" :style="{gridTemplateColumns: (leftCollapsed? '0px' : '320px') + ' 1fr ' + ((codeCollapsed && !chatOnly)? '0px' : '320px')}">
    <header class="topbar">
      <div class="brand">
        <div class="logo">Q</div>
        <div class="title">分类分析演示</div>
      </div>
      <div class="top-actions">
        <input type="file" id="file-input" style="display:none" @change="handleUpload" />
        <button class="btn ghost" v-if="leftCollapsed" @click="toggleLeft">▸ 展开左侧</button>
        <button class="btn ghost" v-if="codeCollapsed" @click="toggleCode">▸ 展开预览</button>
        <button class="btn ghost" @click="triggerUpload">上传文件</button>
        <button class="btn ghost" @click="downloadReport">下载报告</button>
        <button class="btn ghost" @click="toggleChatOnly">{{ chatOnly? '全布局':'仅对话' }}</button>
        <button class="btn ghost" @click="toggleTheme">{{ theme==='light'?'🌙 暗色':'☀️ 亮色' }}</button>
      </div>
    </header>
    <header-nav :current="'code'" />

    <aside class="left" v-show="!leftCollapsed">
      <div class="panel-title strong">
        <span>功能区</span>
        <button class="icon-btn" @click="toggleLeft">{{ leftCollapsed? '▸ 展开左侧':'▾ 收起左侧' }}</button>
      </div>
      <section class="panel">
        <div class="panel-title">项目管理</div>
        <div class="project-controls">
          <button class="btn primary" @click="openProjectManagement">项目管理</button>
          <button class="btn secondary" @click="showStatusInfo">状态</button>
        </div>
      </section>
      <section class="panel" v-if="userId === 'admin'">
        <div class="panel-title">管理员功能</div>
        <div class="project-controls">
          <button class="btn secondary" @click="showAdminPanel = true">用户项目管理</button>
        </div>
      </section>
      <section class="panel">
        <div class="panel-title">文件浏览</div>
        <div class="file-tree">
          <div v-for="node in fileTree" :key="node.id" class="tree-node">
            <div class="node-label" :class="{active: selectedFilePath===node.path}" @click="node.type==='dir'?toggleDir(node):selectFile(node)" @contextmenu="showContextMenu($event, node)">
              <span class="node-icon" v-if="node.type==='dir'">{{ node.expanded? '📂' : '📁' }}</span>
              <span class="node-icon" v-else>📄</span>
              <span v-if="!node.editing">{{ node.name }}</span>
              <input v-else v-model="node.tempName" @blur="finishRename(node)" @keyup.enter="finishRename(node)" @keyup.esc="cancelRename(node)" class="rename-input" :ref="`renameInput_${node.id}`" />
              <div class="node-actions" v-if="!node.editing">
                <button class="dot-btn rename-dot" @click.stop="startRename(node)" title="重命名"></button>
                <button class="dot-btn move-dot" @click.stop="showMoveModal(node)" title="移动"></button>
                <button class="dot-btn delete-dot" @click.stop="deleteNode(node)" title="删除"></button>
              </div>
            </div>
            <div v-if="node.children && node.children.length && node.expanded" class="node-children">
              <div v-for="child in node.children" :key="child.id" class="tree-node">
                <div class="node-label" :class="{active: selectedFilePath===child.path}" @click="selectFile(child)" @contextmenu="showContextMenu($event, child)">
                  <span class="node-icon" v-if="child.type==='dir'">📁</span>
                  <span class="node-icon" v-else>📄</span>
                  <span v-if="!child.editing">{{ child.name }}</span>
                  <input v-else v-model="child.tempName" @blur="finishRename(child)" @keyup.enter="finishRename(child)" @keyup.esc="cancelRename(child)" class="rename-input" :ref="`renameInput_${child.id}`" />
                  <div class="node-actions" v-if="!child.editing">
                    <button class="dot-btn rename-dot" @click.stop="startRename(child)" title="重命名"></button>
                    <button class="dot-btn move-dot" @click.stop="showMoveModal(child)" title="移动"></button>
                    <button class="dot-btn delete-dot" @click.stop="deleteNode(child)" title="删除"></button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </aside>

    <main class="center">
      <section class="code" v-show="!codeCollapsed">
        <div class="code-toolbar">
          <div class="path">{{ selectedFilePath }}</div>
          <div class="tools">
            <button class="icon-btn" @click="toggleCode">{{ codeCollapsed? '▸ 展开预览':'▾ 收起预览' }}</button>
            <input class="search" v-model="searchTextRaw" @keyup.enter="send" placeholder="搜索代码关键字" />
            <button class="icon-btn" @click="fontUp">A+</button>
            <button class="icon-btn" @click="fontDown">A-</button>
            <button class="icon-btn" @click="copyCode">复制代码</button>
            <button class="icon-btn" @click="toggleEditMode" :class="{ 'active': isEditing }">编辑</button>
            <button v-if="isEditing" class="icon-btn" @click="uploadModifiedCode" :disabled="isAnalyzing">上传修改</button>
          </div>
        </div>
        <div class="code-view" :style="{fontSize: fontSize+'px'}" v-show="!codeCollapsed">
          <div class="code-lines">
            <div v-for="(line,i) in filteredCode" :key="i" class="code-line" :class="lineClass(line)" :id="line.fn ? ('line-'+line.fn) : null">
              <div class="label" :class="labelClass(line)" :style="{ backgroundColor: line.tagColor || getTagColor(line.tags) }">
                <span v-if="!isEditing">{{ lineLabel(line) }}</span>
                <select v-else v-model="line.tags" class="tag-select">
                  <option value="">无标签</option>
                  <option value="arm">arm</option>
                  <option value="riscv">riscv</option>
                  <option value="common">通用</option>
                  <option value="custom">自定义</option>
                </select>
                <input v-if="isEditing && line.tags === 'custom'" v-model="line.customTag" placeholder="输入自定义标签" class="custom-tag-input" />
                <input v-if="isEditing" type="color" v-model="line.tagColor" class="color-picker" title="选择标签颜色" />
              </div>
              <div class="gutter" :title="'Line '+ (i+1)">{{ i+1 }}</div>
              <div v-if="isEditing" class="code-editable" contenteditable="true" @input="updateCodeLine(i, $event.target.textContent)" @blur="updateCodeLine(i, $event.target.textContent)">{{ line.text }}</div>
              <pre v-else class="content"><code :class="'language-'+currentLang">{{ line.text }}</code></pre>
            </div>
            <div v-if="filteredCode.length===0" class="empty">未匹配到结果</div>
          </div>
        </div>
      </section>
    </main>

    <aside class="right" v-show="chatOnly || !codeCollapsed">
      <section class="panel">
        <div class="panel-title strong">
          <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
            <span>分类结果统计</span>
            <select v-model="statType" @change="onStatTypeChange" class="stat-type-select">
              <option v-for="type in statTypes" :value="type.value" :key="type.value">{{ type.label }}</option>
            </select>
          </div>
          <div class="panel-actions">
            <button class="icon-btn small" @click="refreshStats">↺</button>
          </div>
        </div>
        <div class="bar-chart">
          <div class="bar-row" v-for="b in barData" :key="b.key">
            <div class="bar-label">{{ b.label }}</div>
            <div class="bar-track">
              <div class="bar" :style="{width: b.percent+'%', background: b.color}"></div>
            </div>
            <div class="bar-count">{{ b.count }}</div>
          </div>
          <div class="bar-note">总行数：{{ totalLines }}；有标签行：{{ taggedLines }}</div>
        </div>
      </section>
      <section class="chat" style="margin-top:12px">
        <div class="section-title">自然语言需求输入</div>
        <div class="chat-history">
          <div class="msg user">
            <div class="avatar">👤</div>
            <div class="bubble">帮我分类 arm/driver.c 的 function 级别，只显示 riscv 相关函数</div>
          </div>
          <div class="msg system">
            <div class="avatar">🅆</div>
            <div class="bubble">已接收需求，正在分析 arm/driver.c 的 function 级别分类，目标架构：riscv</div>
          </div>
          <div class="msg" v-for="m in messages" :key="m.id" :class="m.role">
            <div class="avatar">{{ m.role==='user'?'👤':'🅆' }}</div>
            <div class="bubble">{{ m.text }}</div>
          </div>
        </div>
        <div class="chat-input">
          <textarea v-model="inputText" class="textarea" rows="1" @keydown.enter="onEnter" placeholder="请输入分类需求"></textarea>
          <button class="btn primary" @click="send">发送</button>
        </div>
      </section>
    </aside>
    <div class="toast" v-if="toastVisible">{{ toastText }}</div>
    
    <!-- 移动文件/目录模态框 -->
    <div class="overlay" v-if="showMoveModalFlag" @click="closeMoveModal"></div>
    <div class="move-modal" v-if="showMoveModalFlag" @click.stop>
      <h3>移动 '{{ movingNode ? movingNode.name : '' }}'</h3>
      <div style="margin: 15px 0;">
        <label>选择目标目录:</label>
        <div class="file-tree" style="max-height: 200px; overflow-y: auto; border: 1px solid #eee; padding: 10px; margin-top: 5px;">
          <div v-for="node in fileTree" :key="node.id" class="tree-node">
            <div class="node-label" @click="selectTargetDir(node)">
              <span class="node-icon" v-if="node.type==='dir'">{{ node.expanded? '📂' : '📁' }}</span>
              <span>{{ node.name }}</span>
            </div>
            <div v-if="node.children && node.children.length && node.expanded" class="node-children">
              <div v-for="child in node.children" :key="child.id" class="tree-node">
                <div class="node-label" @click="selectTargetDir(child)">
                  <span class="node-icon" v-if="child.type==='dir'">📁</span>
                  <span>{{ child.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div style="text-align: right; margin-top: 15px;">
        <button class="btn secondary" @click="performMove" :disabled="!selectedTargetDir" style="margin-right: 10px;">移动</button>
        <button class="btn secondary" @click="closeMoveModal">取消</button>
      </div>
    </div>
    
    <!-- 右键菜单 -->
    <div class="context-menu" v-if="showContextMenu" :style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }" @click.stop>
      <div class="context-menu-item" @click="startRename(contextMenuNode)">
        <span class="dot-btn rename-dot"></span>
        <span>重命名</span>
      </div>
      <div class="context-menu-item" @click="showMoveModal(contextMenuNode)">
        <span class="dot-btn move-dot"></span>
        <span>移动</span>
      </div>
      <div class="context-menu-item" @click="deleteNode(contextMenuNode)">
        <span class="dot-btn delete-dot"></span>
        <span>删除</span>
      </div>
    </div>
    
    <!-- 项目管理弹窗 -->
    <div class="overlay" v-if="showProjectModal" @click="closeProjectModal"></div>
    <div class="status-info-panel" v-if="showProjectModal" @click.stop style="min-width: 500px; max-width: 800px;">
      <h3>项目管理</h3>
      <div style="display: flex; gap: 10px; margin-bottom: 15px;">
        <button class="btn primary" @click="uploadProject">上传项目/文件</button>
        <button class="btn secondary" @click="createNewProject">新建项目</button>
        <button class="btn secondary" @click="openExistingProject" :disabled="!selectedProject">打开项目</button>
      </div>
      <div style="margin: 15px 0;">
        <h4>项目列表</h4>
        <div v-if="projects.length === 0" style="padding: 10px; text-align: center; color: #999;">暂无项目</div>
        <div v-else>
          <div v-for="project in projects" :key="project.id" 
               class="project-item" 
               :class="{selected: selectedProject && selectedProject.id === project.id}"
               @click="selectedProject = project"
               style="padding: 8px; border: 1px solid #eee; margin-bottom: 5px; cursor: pointer; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>{{ project.name }}</span>
              <div>
                <button class="dot-btn rename-dot" @click.stop="renameProject" title="重命名"></button>
                <button class="dot-btn delete-dot" @click.stop="deleteProject" title="删除"></button>
              </div>
            </div>
            <small style="color: #999;">路径: {{ project.path }}</small>
          </div>
        </div>
      </div>
      <div style="text-align: right; margin-top: 15px;">
        <button class="btn secondary" @click="closeProjectModal">关闭</button>
      </div>
    </div>
    
    <!-- 状态信息弹窗 -->
    <div class="overlay" v-if="showStatusPanel" @click="closeStatusPanel"></div>
    <div class="status-info-panel" v-if="showStatusPanel" @click.stop style="min-width: 400px;">
      <h3>状态信息</h3>
      <div style="margin: 15px 0;">
        <h4>文件上传状态</h4>
        <div v-if="isUploading">
          <div>上传进度: {{ uploadProgress }}%</div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: uploadProgress + '%' }"></div>
          </div>
        </div>
        <div v-else>
          <div>当前无上传任务</div>
        </div>
      </div>
      <div style="margin: 15px 0;">
        <h4>分析进度状态</h4>
        <div v-if="isAnalyzing">
          <div>分析进度: {{ analysisProgress }}%</div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: analysisProgress + '%' }"></div>
          </div>
        </div>
        <div v-else>
          <div>当前无分析任务</div>
        </div>
      </div>
      <div style="text-align: right; margin-top: 15px;">
        <button class="btn secondary" @click="simulateAnalysis" style="margin-right: 10px;" v-if="!isAnalyzing">模拟开始分析</button>
        <button class="btn secondary" @click="closeStatusPanel">关闭</button>
      </div>
    </div>
  </div>
  
  <!-- 管理员功能弹窗 -->
  <div class="overlay" v-if="showAdminPanel" @click="closeAdminPanel"></div>
  <div class="status-info-panel" v-if="showAdminPanel" @click.stop style="min-width: 500px; max-width: 800px;">
    <h3>管理员控制面板</h3>
    <div style="margin: 15px 0;">
      <h4>用户项目管理</h4>
      <div class="admin-user-list">
        <div class="admin-user-item" v-for="user in adminUsers" :key="user.username">
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; border: 1px solid #eee; margin-bottom: 5px; border-radius: 4px;">
            <div>
              <div><strong>{{ user.username }}</strong> ({{ user.telphone }})</div>
              <div style="font-size: 12px; color: #666;">
                代码文件: {{ user.numFile }}, 标签: {{ user.numTag }}, 标注关系: {{ user.numRelation }}
              </div>
            </div>
            <div>
              <button class="btn danger small" @click="deleteUserProjects(user.username)">删除用户项目</button>
            </div>
          </div>
          
          <!-- 用户项目列表 -->
          <div v-if="user.projects && user.projects.length > 0" style="margin-left: 20px; margin-top: 5px;">
            <div v-for="project in user.projects" :key="project.id" style="display: flex; justify-content: space-between; align-items: center; padding: 6px; background: #f9f9f9; margin-bottom: 3px; border-radius: 3px;">
              <span>{{ project.name }}</span>
              <button class="btn danger small" @click="deleteProjectById(user.username, project.id)">删除项目</button>
            </div>
          </div>
          <div v-else style="margin-left: 20px; font-size: 12px; color: #999; padding: 5px 0;">
            该用户暂无项目
          </div>
        </div>
      </div>
    </div>
    <div style="text-align: right; margin-top: 15px;">
      <button class="btn secondary" @click="closeAdminPanel">关闭</button>
    </div>
  </div>
</template>
<style scoped>
.project-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
}

.project-controls .btn {
  width: 100%;
  margin-bottom: 0;
}

.status-info-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 20px;
  z-index: 1000;
  min-width: 300px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 999;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background-color: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
  margin: 10px 0;
}

.stat-type-select {
  padding: 2px 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 12px;
  background-color: white;
  min-width: 120px;
}

.icon-btn.small {
  width: 24px;
  height: 24px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.bar-chart {
  overflow-x: auto;
}

.bar-row {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  min-height: 24px;
}

.bar-label {
  min-width: 60px;
  font-size: 12px;
  margin-right: 8px;
  white-space: nowrap;
}

.bar-track {
  flex: 1;
  min-width: 100px;
  height: 16px;
  background-color: #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.bar {
  height: 100%;
  transition: width 0.3s ease;
}

.bar-count {
  min-width: 30px;
  text-align: right;
  font-size: 12px;
  margin-left: 8px;
  white-space: nowrap;
}

.bar-note {
  font-size: 12px;
  color: #666;
  margin-top: 8px;
  text-align: center;
  white-space: nowrap;
}

.progress {
  height: 100%;
  background-color: #4da3ff;
  transition: width 0.3s ease;
}

.node-actions {
  display: flex;
  gap: 2px;
  margin-left: auto;
  align-items: center;
}

.rename-input {
  flex: 1;
  padding: 2px 4px;
  border: 1px solid #ccc;
  border-radius: 2px;
  font-size: inherit;
  margin-right: 4px;
}

.move-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 20px;
  z-index: 1001;
  min-width: 300px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.tree-node .icon-btn {
  width: 16px;
  height: 16px;
  padding: 0;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  line-height: 1;
  opacity: 0.6;
  border: none;
  background: transparent;
  margin-left: 2px;
}

.tree-node .icon-btn:hover {
  opacity: 1;
  background-color: #e6f7ff;
  border-radius: 3px;
  border: 1px solid #1890ff;
}

/* 彩色圆点按钮样式 */
.dot-btn {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  margin-left: 4px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.dot-btn:hover {
  opacity: 1;
}

.rename-dot {
  background-color: #FFD700; /* 金色，用于重命名 */
}

.move-dot {
  background-color: #4A90E2; /* 蓝色，用于移动 */
}

.delete-dot {
  background-color: #FF6B6B; /* 红色，用于删除 */
}

/* 修复页面布局，确保HeaderNav组件正确显示 */
.app {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr;
}

header.topbar {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #ffffff;
  border-bottom: 1px solid #e8e8e8;
  position: sticky;
  top: 0;
  z-index: 100;
}

/* 右键菜单中的彩色圆点 */
.context-menu .rename-dot {
  width: 8px;
  height: 8px;
}

.context-menu .move-dot {
  width: 8px;
  height: 8px;
}

.context-menu .delete-dot {
  width: 8px;
  height: 8px;
}

/* 项目管理弹窗中的彩色圆点 */
.project-item .dot-btn {
  margin-left: 6px;
}

/* 代码编辑区域样式 */
.code-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f6f8fa;
  border-bottom: 1px solid #d0d7de;
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

.code-lines {
  background-color: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 0 0 6px 6px;
  overflow-x: auto;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12px;
  line-height: 20px;
}

.code-line {
  display: flex;
  align-items: center;
  padding: 0;
  min-height: 20px;
}

.code-line:hover {
  background-color: #f6f8fa;
}

.gutter {
  padding: 0 8px;
  background-color: #f6f8fa;
  border-right: 1px solid #d0d7de;
  color: #656d76;
  text-align: right;
  min-width: 40px;
  user-select: none;
}

.content {
  margin: 0;
  padding: 0 8px;
  flex: 1;
  white-space: pre;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12px;
}

.code-editable {
  margin: 0;
  padding: 0 8px;
  flex: 1;
  white-space: pre;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12px;
  min-height: 20px;
  outline: none;
  border: 1px solid transparent;
}

.code-editable:focus {
  border: 1px solid #0969da;
  border-radius: 2px;
}

.label {
  padding: 0 6px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 500;
  line-height: 16px;
  text-align: center;
  min-width: 40px;
  margin-right: 4px;
}

.label-arm {
  background-color: #ddf4ff;
  color: #0969da;
}

.label-riscv {
  background-color: #dafbe1;
  color: #2da44e;
}

.label-common {
  background-color: #f3f3f3;
  color: #656d76;
}

.label-custom {
  background-color: #fff8c5;
  color: #9a6700;
}

.tag-select {
  font-size: 11px;
  padding: 2px 4px;
  border: 1px solid #d0d7de;
  border-radius: 2px;
  background-color: white;
}

.custom-tag-input {
  font-size: 11px;
  padding: 2px 4px;
  border: 1px solid #d0d7de;
  border-radius: 2px;
  margin-left: 4px;
  width: 100px;
}

.color-picker {
  width: 20px;
  height: 20px;
  border: none;
  border-radius: 2px;
  cursor: pointer;
  margin-left: 4px;
  padding: 0;
}

.icon-btn.active {
  background-color: #0969da;
  color: white;
  border-radius: 6px;
}

.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 1002;
  padding: 4px 0;
}

.context-menu-item {
  padding: 4px 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.context-menu-item:hover {
  background-color: #f0f0f0;
}

.context-menu-item:disabled {
  color: #ccc;
  cursor: not-allowed;
}

.node-label {
  padding: 2px 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
<script>
import Prism from 'prismjs'
import HeaderNav from '@/components/HeaderNav.vue'
import { projectApi } from '@/api/projectApi.js'

const sampleCode = {
  'arm/driver.c': [
    { text: '#include <stdio.h>', tags: ['common'], customTag: '', tagColor: '#f3f3f3' },
    { text: 'int init_driver() {', tags: ['arm'], type: 'function', fn: 'init_driver', customTag: '', tagColor: '#ddf4ff' },
    { text: '    int ok = 1;', tags: ['arm'], customTag: '', tagColor: '#ddf4ff' },
    { text: '    return ok;', tags: ['arm'], customTag: '', tagColor: '#ddf4ff' },
    { text: '}', tags: ['arm'], customTag: '', tagColor: '#ddf4ff' },
    { text: '', tags: [], customTag: '', tagColor: '' },
    { text: 'int calc_riscv(int x) {', tags: ['riscv'], type: 'function', fn: 'calc_riscv', customTag: '', tagColor: '#dafbe1' },
    { text: '    int res = x;', tags: ['riscv'], customTag: '', tagColor: '#dafbe1' },
    { text: '    if (RISCV_VECTOR) {', tags: ['riscv'], type: 'block', customTag: '', tagColor: '#dafbe1' },
    { text: '        res += 8;', tags: ['riscv'], customTag: '', tagColor: '#dafbe1' },
    { text: '    }', tags: ['riscv'], customTag: '', tagColor: '#dafbe1' },
    { text: '    return res;', tags: ['riscv'], type: 'stmt', customTag: '', tagColor: '#dafbe1' },
    { text: '}', tags: ['riscv'], customTag: '', tagColor: '#dafbe1' },
    { text: '', tags: [], customTag: '', tagColor: '' },
    { text: 'void print_info() {', tags: ['common'], type: 'function', fn: 'print_info', customTag: '', tagColor: '#f3f3f3' },
    { text: '    printf("info\\n");', tags: ['common'], customTag: '', tagColor: '#f3f3f3' },
    { text: '}', tags: ['common'], customTag: '', tagColor: '#f3f3f3' },
  ],
  'arm/global.h': [
    { text: '#pragma once', tags: ['common'], customTag: '', tagColor: '#f3f3f3' },
    { text: '#define RISCV_VECTOR 1', tags: ['common'], customTag: '', tagColor: '#f3f3f3' },
  ]
}

export default {
  components: { HeaderNav },
  data() {
    return {
      fileTree: [
        { id: 'root-arm', name: 'arm', type: 'dir', path: 'arm', expanded: true, editing: false, tempName: 'arm', children: [
          { id: 'arm-driver', name: 'driver.c', type: 'file', path: 'arm/driver.c', editing: false, tempName: 'driver.c' },
          { id: 'arm-global', name: 'global.h', type: 'file', path: 'arm/global.h', editing: false, tempName: 'global.h' }
        ]}
      ],
      selectedFilePath: 'arm/driver.c',
      fontSize: 14,
      messages: [],
      inputText: '',
      searchText: '',
      searchTextRaw: '',
      _searchTimer: null,
      toastText: '',
      toastVisible: false,
      codeCollapsed: false,
      leftCollapsed: false,
      chatOnly: false,
      reportData: null,
      uploadedFiles: [],
      apiBase: 'http://127.0.0.1:5000',
      lastZipFile: null,
      config: { granularity: 'function', level: 'ISA', targetArch: 'all' },
      theme: 'light',
      codeTextMap: {},
      serverStats: null,
      lastReply: '',
      showProjectModal: false,
      showStatusPanel: false,
      showMoveModalFlag: false,  // 控制移动模态框显示
      movingNode: null,        // 正在移动的节点
      selectedTargetDir: null, // 选中的目标目录
      showContextMenu: false,  // 控制右键菜单显示
      contextMenuPosition: { x: 0, y: 0 }, // 右键菜单位置
      contextMenuNode: null,   // 右键点击的节点
      userId: window.localStorage.getItem('userId') || 'demo', // 当前用户ID，用于判断是否为管理员
      showAdminPanel: false, // 是否显示管理员面板
      adminUsers: [ // 管理员用户数据
        { 
          username: 'admin', 
          telphone: '13800138000', 
          numFile: 5, 
          numTag: 10, 
          numRelation: 3, 
          projects: [
            { id: 1, name: '管理系统项目' },
            { id: 2, name: '数据分析项目' }
          ]
        },
        { 
          username: 'user1', 
          telphone: '13800138001', 
          numFile: 3, 
          numTag: 5, 
          numRelation: 2, 
          projects: [
            { id: 3, name: '前端项目' }
          ]
        },
        { 
          username: 'user2', 
          telphone: '13800138002', 
          numFile: 7, 
          numTag: 15, 
          numRelation: 8, 
          projects: [
            { id: 4, name: '后端项目' },
            { id: 5, name: 'API项目' },
            { id: 6, name: '测试项目' }
          ]
        }
      ],
      uploadProgress: 0,
      analysisProgress: 0,
      isUploading: false,
      isAnalyzing: false,
      projects: [],
      selectedProject: null,
      statusInterval: null,
      isEditing: false,         // 是否处于编辑模式
      statType: 'architecture', // 统计类型，默认为架构统计
      statTypes: [              // 可选的统计类型
        { value: 'architecture', label: '架构分布统计' },
        { value: 'function', label: '函数级别统计' },
        { value: 'file', label: '文件级别统计' },
        { value: 'custom', label: '自定义统计' }
      ],
      serverBarData: null,      // 服务器返回的统计图表数据
    }
  },
  computed: {
    currentCode() { return sampleCode[this.selectedFilePath] || [] },
    filteredCode() {
      const text = this.searchText.trim().toLowerCase()
      if (!text) return this.currentCode
      return this.currentCode.filter(l => (l.text || '').toLowerCase().includes(text))
    },
    stats() {
      if (this.serverStats) return this.serverStats
      const lines = this.currentCode
      const funcs = lines.filter(l => l.type === 'function')
      const funcCount = funcs.length
      const riscvFuncCount = funcs.filter(l => (l.tags || []).includes('riscv')).length
      let fileArch = '通用'
      const hasArm = lines.some(l => (l.tags || []).includes('arm'))
      const hasRiscv = lines.some(l => (l.tags || []).includes('riscv'))
      if (hasArm && hasRiscv) fileArch = '混合'
      else if (hasArm) fileArch = 'arm'
      else if (hasRiscv) fileArch = 'riscv'
      return { funcCount, riscvFuncCount, fileArch }
    },
    totalLines() { return this.currentCode.length },
    taggedLines() { return this.currentCode.filter(l => (l.tags||[]).length).length },
    barData() {
      // 如果有服务器返回的统计图表数据，优先使用
      if (this.serverBarData) {
        return this.serverBarData;
      }
      
      // 根据选择的统计类型返回相应数据
      switch(this.statType) {
        case 'architecture':
          // 架构分布统计 - 返回图1的示例数据
          if (this.serverStats && this.serverStats.counts) {
            const counts = this.serverStats.counts
            const total = Math.max(1, (counts.arm||0)+(counts.riscv||0)+(counts.common||0))
            const toPercent = (n) => Math.round((n/total)*100)
            return [
              { key:'arm', label:'ARM', count:counts.arm||0, percent:toPercent(counts.arm||0), color:'var(--arm-color, #4da3ff)' },
              { key:'riscv', label:'RISC-V', count:counts.riscv||0, percent:toPercent(counts.riscv||0), color:'var(--riscv-color, #5ccf73)' },
              { key:'common', label:'通用', count:counts.common||0, percent:toPercent(counts.common||0), color:'#b0b0b0' }
            ]
          }
          // 默认数据
          return [
            { key:'arm', label:'ARM', count:25, percent:35, color:'var(--arm-color, #4da3ff)' },
            { key:'riscv', label:'RISC-V', count:30, percent:40, color:'var(--riscv-color, #5ccf73)' },
            { key:'common', label:'通用', count:18, percent:25, color:'#b0b0b0' }
          ];
          
        case 'function':
          // 函数级别统计 - 返回图2的示例数据
          return [
            { key:'func_arm', label:'ARM函数', count:8, percent:30, color:'var(--arm-color, #4da3ff)' },
            { key:'func_riscv', label:'RISC-V函数', count:10, percent:40, color:'var(--riscv-color, #5ccf73)' },
            { key:'func_common', label:'通用函数', count:7, percent:30, color:'#b0b0b0' }
          ];
          
        case 'file':
          // 文件级别统计 - 返回图3的示例数据
          return [
            { key:'file_arm', label:'ARM行', count:45, percent:35, color:'var(--arm-color, #4da3ff)' },
            { key:'file_riscv', label:'RISC-V行', count:55, percent:45, color:'var(--riscv-color, #5ccf73)' },
            { key:'file_common', label:'通用行', count:25, percent:20, color:'#b0b0b0' }
          ];
          
        case 'custom':
          // 自定义统计
          return [
            { key:'tag1', label:'标签1', count:15, percent:25, color:'#4da3ff' },
            { key:'tag2', label:'标签2', count:20, percent:30, color:'#5ccf73' },
            { key:'tag3', label:'标签3', count:18, percent:25, color:'#b0b0b0' },
            { key:'tag4', label:'标签4', count:12, percent:20, color:'#ffa500' }
          ];
          
        default:
          // 默认返回架构统计
          return [
            { key:'arm', label:'ARM', count:25, percent:35, color:'var(--arm-color, #4da3ff)' },
            { key:'riscv', label:'RISC-V', count:30, percent:40, color:'var(--riscv-color, #5ccf73)' },
            { key:'common', label:'通用', count:18, percent:25, color:'#b0b0b0' }
          ];
      }
    },
    currentLang() {
      const p = this.selectedFilePath || ''
      const ext = p.split('.').pop().toLowerCase()
      if (['c','h','cpp','cc','cxx'].includes(ext)) return 'c'
      if (['js','ts','jsx','tsx','java','go','rs'].includes(ext)) return 'clike'
      if (['py'].includes(ext)) return 'clike'
      return 'c'
    },
    chatHeight() { if (this.codeCollapsed) return 100; if (this.leftCollapsed) return 60; return 30 }
  },
  methods: {
    selectFile(node) { if (node.type === 'file') { this.selectedFilePath = node.path } },
    toggleDir(node) { node.expanded = !node.expanded },
    toggleCode() { this.codeCollapsed = !this.codeCollapsed },
    toggleLeft() { this.leftCollapsed = !this.leftCollapsed },
    toggleChatOnly() { this.chatOnly = !this.chatOnly; if (this.chatOnly) { this.leftCollapsed = true; this.codeCollapsed = true } else { this.leftCollapsed = false; this.codeCollapsed = false } },
    onEnter(e) { if (e.shiftKey) return; e.preventDefault(); this.send() },
    triggerUpload() { const el = document.getElementById('file-input'); if (el) el.click() },
    async handleUpload(e) {
      const f = e.target.files && e.target.files[0]
      if (!f) return
      
      // 更新上传状态
      this.isUploading = true;
      this.uploadProgress = 0;
      
      const isZip = /\.zip$/i.test(f.name)
      if (isZip) { 
        this.lastZipFile = null; 
        this.toast('暂不支持项目包上传'); 
        e.target.value = ''; 
        this.isUploading = false;
        return 
      }
      
      const reader = new FileReader()
      reader.onload = async () => {
        const text = String(reader.result || '')
        const lines = text.split(/\r?\n/)
        const parsed = lines.map((s) => ({ text: s || '', tags: [], tagColor: '', customTag: '' }))
        const path = 'uploaded/' + f.name
        this.codeTextMap[path] = text
        sampleCode[path] = parsed
        let uploadedRoot = this.fileTree.find(n => n.path === 'uploaded')
        if (!uploadedRoot) { 
          uploadedRoot = { 
            id: 'root-uploaded', 
            name: 'uploaded', 
            type: 'dir', 
            path: 'uploaded', 
            expanded: true, 
            editing: false, 
            tempName: 'uploaded',
            children: [] 
          }; 
          this.fileTree.push(uploadedRoot) 
        }
        uploadedRoot.children.push({ 
          id: 'uploaded-' + Date.now(), 
          name: f.name, 
          type: 'file', 
          path, 
          editing: false, 
          tempName: f.name 
        })
        this.selectedFilePath = path
        this.codeCollapsed = false
        this.$nextTick(() => Prism.highlightAll())
        
        // 更新上传进度
        this.uploadProgress = 100;
        
        // 开始分析并更新分析状态
        this.isAnalyzing = true;
        this.analysisProgress = 0;
        
        // 模拟分析进度
        const analysisInterval = setInterval(() => {
          if (this.analysisProgress < 90) {
            this.analysisProgress += 5;
          }
        }, 100);
        
        await this.analyze(f.name, text)
        
        clearInterval(analysisInterval);
        this.analysisProgress = 100;
        
        // 任务完成后更新状态
        setTimeout(() => {
          this.isUploading = false;
          this.isAnalyzing = false;
        }, 500);
      }
      reader.readAsText(f)
      e.target.value = ''
    },
    async deleteFile(node) {
      this.performDelete(node);
    },
    async downloadReport() {
      const codeId = (this.selectedFilePath || '').split('/').pop() || 'report'
      if (this.reportData) {
        const content = typeof this.reportData === 'string' ? this.reportData : JSON.stringify(this.reportData)
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = codeId + '.report.txt'
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
        this.toast('报告下载成功')
        return
      }
      try {
        const base = (this.apiBase || '').replace(/\+$/, '')
        const fd = new FormData()
        fd.append('userId', this.userId || 'demo')
        fd.append('codeId', codeId)
        const r = await fetch(base + '/Code/report', { method: 'POST', body: fd })
        if (r && r.ok) {
          const blob = await r.blob()
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = codeId + '.report.txt'
          document.body.appendChild(a)
          a.click()
          a.remove()
          URL.revokeObjectURL(url)
          this.toast('报告下载成功')
          return
        }
        this.toast('后端报告生成失败，使用前端备用报告')
        this.backupDownloadReport()
      } catch (_) {
        this.toast('后端报告生成失败，使用前端备用报告')
        this.backupDownloadReport()
      }
    },
    backupDownloadReport() {
      const content = this.reportData ? JSON.stringify(this.reportData) : this.buildReport()
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const base = (this.selectedFilePath || 'report').split('/').pop()
      a.download = base + '.report.txt'
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    },
    buildReport() {
      const lines = this.currentCode
      const funcs = lines.filter(l => l.type === 'function')
      const list = funcs.map(l => {
        let tag = 'common';
        if (Array.isArray(l.tags)) {
          tag = l.tags[0] || 'common';
        } else if (typeof l.tags === 'string') {
          tag = l.tags || 'common';
        }
        if (tag === 'custom' && l.customTag) {
          tag = l.customTag;
        }
        const color = l.tagColor || 'default';
        return `${l.fn || 'unknown'} | ${tag} | ${color}`;
      });
      const s = this.stats
      const conf = this.config
      return [
        `file: ${this.selectedFilePath}`,
        `arch: ${s.fileArch}`,
        `granularity: ${conf.granularity}`,
        `level: ${conf.level}`,
        `targetArch: ${conf.targetArch}`,
        `funcCount: ${s.funcCount}`,
        `riscvFuncCount: ${s.riscvFuncCount}`,
        `functions:`,
        ...list
      ].join('\n')
    },
    async send() {
      if (!this.inputText.trim()) return
      const userMsgId = Date.now() + '-u'
      this.messages.push({ id: userMsgId, role: 'user', text: this.inputText })
      const loadingId = Date.now() + '-loading'
      this.messages.push({ id: loadingId, role: 'system', text: '分析中…' })
      const codeId = (this.selectedFilePath || '').split('/').pop() || 'code.c'
      const text = this.codeTextMap[this.selectedFilePath] || this.currentCode.map(l => l.text).join('\n')
      const ok = await this.analyze(codeId, text)
      const idx = this.messages.findIndex(m => m.id === loadingId)
      if (idx >= 0) {
        const reply = (ok && this.lastReply) ? this.lastReply : `已接收需求，正在分析 ${this.selectedFilePath}`
        this.messages.splice(idx, 1, { id: loadingId + '-done', role: 'system', text: reply })
      }
      this.inputText = ''
      this.$nextTick(() => { const box = document.querySelector('.chat-history'); if (box) box.scrollTop = box.scrollHeight })
    },
    async analyze(codeId, codeText) {
      try {
        // 设置分析状态
        this.isAnalyzing = true;
        this.analysisProgress = 0;
        
        // 模拟分析进度
        const analysisInterval = setInterval(() => {
          if (this.analysisProgress < 90) {
            this.analysisProgress += 2;
          }
        }, 100);
        
        const base = (this.apiBase || '').replace(/\+$/, '')
        const fd = new FormData()
        const ext = (codeId.split('.').pop() || 'c').toLowerCase()
        fd.append('userId', this.userId || 'demo')
        fd.append('codeId', codeId)
        fd.append('code', codeText || '')
        fd.append('language', ['c','h','cpp','cc','cxx','py','js','ts','java','go','rs'].includes(ext) ? ext : 'c')
        fd.append('prompt', this.inputText || '')
        if (!this.inputText){
          const r = await fetch(base + '/Analysis/analyze', { method: 'POST', body: fd })
          clearInterval(analysisInterval);
          this.analysisProgress = 100;
          if (!r || !r.ok) { 
            this.toast('后端分析失败，保留未标注预览'); 
            this.isAnalyzing = false;
            return false 
          }
          const data = await r.json().catch(() => null)
          if (!data || data.state !== 'success' || !data.rst) { 
            this.toast('后端分析失败，保留未标注预览'); 
            this.isAnalyzing = false;
            return false 
          }
          const { reply, annotations, report, stats, codeContent } = data.rst
          this.lastReply = reply || ''
          this.applyAnnotations(this.selectedFilePath, annotations || [])
          this.reportData = report || null
          this.serverStats = stats || null
          
          // 如果后端返回了完整的代码内容，也要同步更新
          if (codeContent) {
            this.updateCodeFromBackend(this.selectedFilePath, codeContent)
          }
        }
        else{
          const r = await fetch(base + '/Analysis/chat', { method: 'POST', body: fd })
          clearInterval(analysisInterval);
          this.analysisProgress = 100;
          if (!r || !r.ok) { 
            this.toast('后端分析失败，保留未标注预览'); 
            this.isAnalyzing = false;
            return false 
          }
          const data = await r.json().catch(() => null)
          if (!data || data.state !== 'success' || !data.rst) { 
            this.toast('后端分析失败，保留未标注预览'); 
            this.isAnalyzing = false;
            return false 
          }
          this.lastReply = data.rst
          this.isAnalyzing = false;
          return true
        }
        this.$nextTick(() => Prism.highlightAll())
        this.toast('分析完成，已应用标注与统计')
        
        // 结束分析状态
        setTimeout(() => {
          this.isAnalyzing = false;
        }, 500);
        
        return true
      } catch (_) {
        this.toast('后端分析异常，保留未标注预览')
        this.isAnalyzing = false;
        return false
      }
    },
    applyAnnotations(path, annotations) {
      const lines = sampleCode[path] || []
      annotations.forEach(a => {
        const i = typeof a.line === 'number' ? a.line - 1: (typeof a.index === 'number' ? a.index : -1)
        if (i >= 0 && i < lines.length) {
          const tags = Array.isArray(a.tags) ? a.tags : (a.tag ? [a.tag] : [])
          // 使用后端返回的标签颜色，如果没有则使用默认颜色
          let tagColor = a.tagColor || lines[i].tagColor || '';
          if (!tagColor && tags.length > 0) {
            tagColor = this.getDefaultTagColor(tags[0]);
          }
          lines[i] = Object.assign({}, lines[i], { 
            tags, 
            customTag: a.customTag || lines[i].customTag || '', 
            tagColor, 
            type: a.type, 
            fn: a.fn 
          })
        }
      })
    },
    
    // 根据标签获取默认颜色
    getDefaultTagColor(tag) {
      const colorMap = {
        'arm': '#ddf4ff',
        'riscv': '#dafbe1',
        'common': '#f3f3f3',
        'x86': '#ffeaa7',
        'mips': '#a29bfe',
        'default': '#ffffff'
      };
      return colorMap[tag] || colorMap['default'];
    },
    
    // 根据后端返回的完整代码内容更新前端显示
    updateCodeFromBackend(path, codeContent) {
      if (!sampleCode[path]) return;
      
      // 如果codeContent是字符串，将其分割为行
      let lines = [];
      if (typeof codeContent === 'string') {
        lines = codeContent.split('\n');
      } else if (Array.isArray(codeContent)) {
        // 如果codeContent是数组，直接使用
        lines = codeContent;
      } else {
        // 如果codeContent是对象数组（包含text、tags等），直接赋值
        sampleCode[path] = codeContent;
        this.updateCodeDisplay(path);
        return;
      }
      
      // 更新代码内容，保留原有的标签信息
      const updatedLines = lines.map((lineText, index) => {
        const existingLine = sampleCode[path][index] || {};
        return {
          text: lineText,
          tags: existingLine.tags || [],
          tagColor: existingLine.tagColor || '',
          customTag: existingLine.customTag || '',
          type: existingLine.type,
          fn: existingLine.fn
        };
      });
      
      sampleCode[path] = updatedLines;
      this.updateCodeDisplay(path);
    },
    fontUp() { this.fontSize = Math.min(22, this.fontSize + 1) },
    fontDown() { this.fontSize = Math.max(10, this.fontSize - 1) },
    copyCode() { const text = this.currentCode.map(l => l.text).join('\n'); navigator.clipboard.writeText(text); this.toast('已复制当前代码') },
    lineClass(line) {
      const target = this.config.targetArch
      const showAll = target === 'all'
      
      // 处理tags字段，兼容数组和字符串形式
      let tagList = [];
      if (Array.isArray(line.tags)) {
        tagList = line.tags;
      } else if (typeof line.tags === 'string') {
        tagList = [line.tags];
      } else {
        tagList = [];
      }
      
      const hasArm = tagList.includes('arm')
      const hasRiscv = tagList.includes('riscv')
      const hasCommon = tagList.includes('common')
      const gran = this.config.granularity
      const isFunction = line.type === 'function'
      const isBlock = line.type === 'block'
      const isStmt = line.type === 'stmt'
      let match = false
      if (showAll) match = hasArm || hasRiscv || hasCommon
      else if (target === 'arm') match = hasArm
      else if (target === 'riscv') match = hasRiscv
      else if (target === 'common') match = hasCommon
      else match = false
      if (!match) return ''
      if (gran === 'file') return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : hasCommon ? 'line-common' : ''
      if (gran === 'function' && isFunction) return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : hasCommon ? 'line-common' : ''
      if (gran === 'block' && isBlock) return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : hasCommon ? 'line-common' : ''
      if (gran === 'stmt' && isStmt) return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : hasCommon ? 'line-common' : ''
      if (gran === 'mixed') return hasArm ? 'line-arm' : hasRiscv ? 'line-riscv' : hasCommon ? 'line-common' : ''
      return ''
    },
    labelClass(line){
      let t = ''
      if (Array.isArray(line.tags)) {
        t = line.tags[0] || ''
      } else {
        t = line.tags || ''
      }
      if (t==='arm') return 'label-arm'
      if (t==='riscv') return 'label-riscv'
      if (t==='common') return 'label-common'
      if (t==='custom' && line.customTag) return 'label-custom'
      return 'label-empty'
    },
    lineLabel(line){
      if (Array.isArray(line.tags)) {
        const t = line.tags[0] || ''
        if (!t) return ''
        if (t === 'common') return '通用'
        if (t === 'custom' && line.customTag) return line.customTag
        return t
      } else {
        // 如果不是数组而是字符串
        if (!line.tags) return ''
        if (line.tags === 'common') return '通用'
        if (line.tags === 'custom' && line.customTag) return line.customTag
        return line.tags
      }
    },
    getTagColor(tags) {
      let tag = '';
      if (Array.isArray(tags)) {
        tag = tags[0] || '';
      } else {
        tag = tags || '';
      }
      
      switch(tag) {
        case 'arm':
          return '#ddf4ff';
        case 'riscv':
          return '#dafbe1';
        case 'common':
          return '#f3f3f3';
        default:
          return '#ffffff';
      }
    },
    refreshStats(){ this.$nextTick(() => {}) },
    toast(text) { this.toastText = text; this.toastVisible = true; clearTimeout(this._toastTimer); this._toastTimer = setTimeout(() => { this.toastVisible = false }, 1200) },
    toggleTheme() { this.theme = this.theme === 'light' ? 'dark' : 'light'; document.documentElement.setAttribute('data-theme', this.theme); localStorage.setItem('theme', this.theme) },
    async openProjectManagement() {
      try {
        // 获取项目列表
        const response = await projectApi.getProjectList({ userId: this.userId || 'demo' });
        if (response.state === 'success') {
          this.projects = response.rst || [];
        } else {
          this.projects = [];
        }
        this.showProjectModal = true;
      } catch (error) {
        console.error('Failed to load projects:', error);
        // 如果API失败，使用空数组
        this.projects = [];
        this.showProjectModal = true;
        this.toast('获取项目列表失败');
      }
    },
    async showStatusInfo() {
      // 初始化时获取最新状态
      await this.fetchCurrentStatus();
      this.showStatusPanel = true;
    },
    async createNewProject() {
      const projectName = prompt('请输入项目名称:');
      if (!projectName) return;
      
      try {
        const response = await projectApi.createProject({ 
          userId: this.userId || 'demo', 
          projectName: projectName 
        });
        
        if (response.state === 'success') {
          this.toast(`项目 ${projectName} 创建成功`);
          await this.loadProjects();
        } else {
          this.toast(response.description || '创建项目失败');
        }
      } catch (error) {
        console.error('Failed to create project:', error);
        this.toast('创建项目失败');
      }
    },
    async openExistingProject() {
      if (!this.selectedProject) {
        this.toast('请选择一个项目');
        return;
      }
      
      try {
        const response = await projectApi.openProject({ 
          userId: this.userId || 'demo', 
          projectId: this.selectedProject.id 
        });
        
        if (response.state === 'success') {
          this.toast(`项目 ${this.selectedProject.name} 已打开`);
          this.showProjectModal = false;
          // 这里可能需要更新文件树等界面内容
        } else {
          this.toast(response.description || '打开项目失败');
        }
      } catch (error) {
        console.error('Failed to open project:', error);
        this.toast('打开项目失败');
      }
    },
    async deleteProject() {
      if (!this.selectedProject) {
        this.toast('请选择一个项目');
        return;
      }
      
      if (!confirm(`确定要删除项目 ${this.selectedProject.name} 吗？`)) {
        return;
      }
      
      try {
        const response = await projectApi.deleteProject({ 
          userId: this.userId || 'demo', 
          projectId: this.selectedProject.id 
        });
        
        if (response.state === 'success') {
          this.toast(`项目 ${this.selectedProject.name} 已删除`);
          await this.loadProjects();
        } else {
          this.toast(response.description || '删除项目失败');
        }
      } catch (error) {
        console.error('Failed to delete project:', error);
        this.toast('删除项目失败');
      }
    },
    async renameProject() {
      if (!this.selectedProject) {
        this.toast('请选择一个项目');
        return;
      }
      
      const newName = prompt('请输入新的项目名称:', this.selectedProject.name);
      if (!newName) return;
      
      try {
        const response = await projectApi.renameProject({ 
          userId: this.userId || 'demo', 
          projectId: this.selectedProject.id,
          newName: newName
        });
        
        if (response.state === 'success') {
          this.toast(`项目已重命名为 ${newName}`);
          await this.loadProjects();
        } else {
          this.toast(response.description || '重命名项目失败');
        }
      } catch (error) {
        console.error('Failed to rename project:', error);
        this.toast('重命名项目失败');
      }
    },
    async loadProjects() {
      try {
        const response = await projectApi.getProjectList({ userId: this.userId || 'demo' });
        if (response.state === 'success') {
          this.projects = response.rst || [];
        } else {
          this.projects = [];
        }
      } catch (error) {
        console.error('Failed to load projects:', error);
        this.projects = [];
        this.toast('获取项目列表失败');
      }
    },
    async uploadProject() {
      const fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.zip,.rar,.tar,.gz,.tar.gz';
      fileInput.multiple = true; // 允许选择多个文件
      fileInput.onchange = async (event) => {
        const files = event.target.files;
        if (!files || files.length === 0) return;
        
        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          
          try {
            this.isUploading = true;
            this.uploadProgress = 0;
            
            // 创建FormData对象
            const formData = new FormData();
            formData.append('userId', this.userId || 'demo');
            formData.append('projectFile', file);
            
            // 模拟上传进度
            const interval = setInterval(() => {
              if (this.uploadProgress < 90) {
                this.uploadProgress += 5;
              }
            }, 100);
            
            try {
              // 调用API上传项目
              const response = await projectApi.uploadProject(formData);
              
              clearInterval(interval);
              this.uploadProgress = 100;
              
              if (response.state === 'success') {
                this.toast(`项目 ${file.name} 上传成功`);
                await this.loadProjects();
              } else {
                this.toast(response.description || `项目 ${file.name} 上传失败`);
              }
            } catch (error) {
              clearInterval(interval);
              console.error('Failed to upload project:', error);
              this.toast(`项目 ${file.name} 上传失败`);
            } finally {
              this.isUploading = false;
            }
          } catch (error) {
            console.error('Error processing file:', error);
            this.isUploading = false;
            this.toast(`处理文件 ${file.name} 时出错`);
          }
        }
      };
      fileInput.click();
    },
    closeProjectModal() {
      this.showProjectModal = false;
    },
    closeStatusPanel() {
      this.showStatusPanel = false;
    },
    async fetchCurrentStatus() {
      try {
        // 获取上传进度
        const uploadResponse = await projectApi.getUploadProgress({ userId: this.userId || 'demo' });
        if (uploadResponse.state === 'success' && uploadResponse.rst) {
          this.uploadProgress = uploadResponse.rst.progress || 0;
          this.isUploading = uploadResponse.rst.isUploading || false;
        }
        
        // 获取分析进度
        const analysisResponse = await projectApi.getAnalysisProgress({ userId: this.userId || 'demo' });
        if (analysisResponse.state === 'success' && analysisResponse.rst) {
          this.analysisProgress = analysisResponse.rst.progress || 0;
          this.isAnalyzing = analysisResponse.rst.isAnalyzing || false;
        }
      } catch (error) {
        console.error('Failed to fetch status:', error);
        // 即使API失败也不显示错误，因为这只是一个状态查询
      }
    },
    simulateAnalysis() {
      this.isAnalyzing = true;
      this.analysisProgress = 0;
      
      const interval = setInterval(() => {
        if (this.analysisProgress < 100) {
          this.analysisProgress += 10;
        } else {
          clearInterval(interval);
          this.isAnalyzing = false;
          this.toast('分析完成');
        }
      }, 300);
    },
    
    // 目录树节点操作相关方法
    startRename(node) {
      // 开始重命名模式
      node.editing = true;
      node.tempName = node.name;
      this.$nextTick(() => {
        const inputRef = this.$refs[`renameInput_${node.id}`];
        if (inputRef && inputRef[0]) {
          inputRef[0].focus();
        }
      });
    },
    finishRename(node) {
      if (!node.tempName || node.tempName.trim() === '') {
        this.toast('名称不能为空');
        return;
      }
      
      // 发送重命名请求到后端
      this.performRename(node, node.tempName);
      
      // 结束编辑模式
      node.editing = false;
    },
    cancelRename(node) {
      // 取消重命名，恢复原名称
      node.editing = false;
    },
    async performRename(node, newName) {
      const oldName = node.name;
      const oldPath = node.path;
      
      try {
        // 更新本地数据
        node.name = newName;
        
        if (node.path) {
          // 如果是文件，更新路径并可能需要更新sampleCode中的键
          if (node.type === 'file') {
            const pathParts = node.path.split('/');
            pathParts[pathParts.length - 1] = newName;
            const newPath = pathParts.join('/');
            
            // 更新sampleCode中的键（如果有）
            if (sampleCode[oldPath]) {
              const codeData = sampleCode[oldPath];
              delete sampleCode[oldPath];
              sampleCode[newPath] = codeData;
              
              // 如果当前选中的文件路径是旧路径，更新它
              if (this.selectedFilePath === oldPath) {
                this.selectedFilePath = newPath;
              }
            }
            
            node.path = newPath;
          } else if (node.type === 'dir') {
            // 如果是目录，需要更新自己及所有子节点的路径
            const pathParts = node.path.split('/');
            pathParts[pathParts.length - 1] = newName;
            const newDirPath = pathParts.join('/');
            
            // 更新目录本身路径
            node.path = newDirPath;
            
            // 递归更新子节点路径
            if (node.children) {
              this.updateNodePath(node, newDirPath);
            }
            
            // 如果当前选中的文件在该目录下，也需要更新
            if (this.selectedFilePath && this.selectedFilePath.startsWith(oldPath + '/')) {
              this.selectedFilePath = this.selectedFilePath.replace(oldPath + '/', newDirPath + '/');
            }
          }
        }
        
        this.toast(`${node.type === 'dir' ? '目录' : '文件'}已重命名为 ${newName}`);
      } catch (error) {
        console.error('Failed to rename node:', error);
        // 回滚更改
        node.name = oldName;
        if (oldPath) node.path = oldPath;
        this.toast(`重命名${node.type === 'dir' ? '目录' : '文件'}失败`);
      }
    },
    deleteNode(node) {
      if (!confirm(`确定要删除${node.type === 'dir' ? '目录' : '文件'} '${node.name}' 吗？`)) {
        return;
      }
      
      this.performDelete(node);
    },
    async performDelete(node) {
      try {
        // 如果是文件，需要同时删除sampleCode中的对应数据和后端存储
        if (node.type === 'file') {
          const base = (this.apiBase || '').replace(/\\+/, '')
          const fd = new FormData()
          fd.append('userId', this.userId || 'demo')
          fd.append('codeId', node.name)
          await fetch(base + '/Code/removeCode', { method: 'POST', body: fd }).catch(() => {})
          
          // 从sampleCode中删除
          delete sampleCode[node.path]
          
          // 如果是当前选中的文件，切换到其他文件
          if (this.selectedFilePath === node.path) {
            const parent = this.findParentNode(node);
            if (parent && parent.children) {
              const remainingChildren = parent.children.filter(child => child.id !== node.id);
              if (remainingChildren.length > 0) {
                this.selectedFilePath = remainingChildren[0].path;
              } else {
                // 如果父目录没有其他文件，尝试切换到其他目录
                const otherFile = this.getFirstAvailableFile();
                this.selectedFilePath = otherFile || 'arm/driver.c';
              }
            }
          }
        }
        
        // 从本地数据中移除
        const parent = this.findParentNode(node);
        if (parent) {
          parent.children = parent.children.filter(child => child.id !== node.id);
        } else {
          // 如果是根节点，则从fileTree中移除
          this.fileTree = this.fileTree.filter(item => item.id !== node.id);
        }
        
        this.$nextTick(() => Prism.highlightAll());
        this.toast(`${node.type === 'dir' ? '目录' : '文件'}已删除`);
      } catch (error) {
        console.error('Failed to delete node:', error);
        this.toast(`删除${node.type === 'dir' ? '目录' : '文件'}失败`);
      }
    },
    findParentNode(targetNode) {
      for (const item of this.fileTree) {
        if (item.children && item.children.some(child => child.id === targetNode.id)) {
          return item;
        }
        
        // 深度搜索
        if (item.children) {
          for (const child of item.children) {
            if (child.children && child.children.some(grandChild => grandChild.id === targetNode.id)) {
              return child;
            }
          }
        }
      }
      return null;
    },
    getFirstAvailableFile() {
      // 查找第一个可用的文件
      for (const item of this.fileTree) {
        if (item.children) {
          for (const child of item.children) {
            if (child.type === 'file' && child.path) {
              return child.path;
            }
            
            // 深度搜索
            if (child.children) {
              for (const grandChild of child.children) {
                if (grandChild.type === 'file' && grandChild.path) {
                  return grandChild.path;
                }
              }
            }
          }
        }
      }
      return null;
    },
    showMoveModal(node) {
      this.movingNode = node;
      this.selectedTargetDir = null;
      this.showMoveModalFlag = true;
    },
    closeMoveModal() {
      this.showMoveModalFlag = false;
      this.movingNode = null;
      this.selectedTargetDir = null;
    },
    selectTargetDir(dir) {
      if (dir.type !== 'dir') {
        // 如果点击的是文件，尝试找到其父目录
        const parent = this.findParentNode(dir);
        if (parent && parent.type === 'dir') {
          this.selectedTargetDir = parent;
        }
        return;
      }
      
      // 确保不能移动到自身或其子目录
      if (this.movingNode.id === dir.id || this.isDescendant(this.movingNode, dir)) {
        this.toast('不能移动到自身或子目录中');
        return;
      }
      
      this.selectedTargetDir = dir;
    },
    isDescendant(child, parent) {
      // 检查child是否是parent的后代
      if (parent.children) {
        for (const item of parent.children) {
          if (item.id === child.id) return true;
          if (this.isDescendant(child, item)) return true;
        }
      }
      return false;
    },
    async performMove() {
      if (!this.movingNode || !this.selectedTargetDir) {
        this.toast('请选择要移动的项和目标目录');
        return;
      }
      
      try {
        // 从原父级移除
        const oldParent = this.findParentNode(this.movingNode);
        if (oldParent) {
          oldParent.children = oldParent.children.filter(child => child.id !== this.movingNode.id);
        } else {
          // 如果是根节点
          this.fileTree = this.fileTree.filter(item => item.id !== this.movingNode.id);
        }
        
        // 添加到新父级
        if (!this.selectedTargetDir.children) {
          this.selectedTargetDir.children = [];
        }
        this.selectedTargetDir.children.push(this.movingNode);
        
        // 更新路径
        if (this.movingNode.path) {
          const newPath = `${this.selectedTargetDir.path}/${this.movingNode.name}`;
          this.updateNodePath(this.movingNode, newPath);
        }
        
        this.toast(`${this.movingNode.type === 'dir' ? '目录' : '文件'}已移动到'${this.selectedTargetDir.name}'`);
        this.closeMoveModal();
      } catch (error) {
        console.error('Failed to move node:', error);
        this.toast(`移动${this.movingNode.type === 'dir' ? '目录' : '文件'}失败`);
      }
    },
    updateNodePath(node, newPath) {
      // 保存旧路径
      const oldPath = node.path;
      
      // 更新节点路径
      node.path = newPath;
      
      // 如果是文件，需要更新sampleCode中的键
      if (node.type === 'file' && sampleCode[oldPath]) {
        const codeData = sampleCode[oldPath];
        delete sampleCode[oldPath];
        sampleCode[newPath] = codeData;
        
        // 如果当前选中的文件是这个文件，也要更新
        if (this.selectedFilePath === oldPath) {
          this.selectedFilePath = newPath;
        }
      } else if (node.type === 'dir') {
        // 如果是目录，也要更新当前选中路径（如果它在移动的目录下）
        if (this.selectedFilePath && this.selectedFilePath.startsWith(oldPath + '/')) {
          this.selectedFilePath = this.selectedFilePath.replace(oldPath + '/', newPath + '/');
        }
      }
      
      // 递归更新子节点路径
      if (node.children) {
        for (const child of node.children) {
          if (child.path) {
            const childPath = `${newPath}/${child.name}`;
            this.updateNodePath(child, childPath);
          }
        }
      }
    },
    
    // 右键菜单相关方法
    showContextMenu(event, node) {
      event.preventDefault();
      this.contextMenuNode = node;
      this.contextMenuPosition.x = event.clientX;
      this.contextMenuPosition.y = event.clientY;
      this.showContextMenu = true;
      
      // 监听页面点击事件来隐藏菜单
      document.addEventListener('click', this.hideContextMenu);
    },
    hideContextMenu() {
      this.showContextMenu = false;
      document.removeEventListener('click', this.hideContextMenu);
    },
    
    // 编辑模式相关方法
    toggleEditMode() {
      this.isEditing = !this.isEditing;
    },
    updateCodeLine(index, newText) {
      if (this.selectedFilePath) {
        const lines = sampleCode[this.selectedFilePath];
        if (lines && index >= 0 && index < lines.length) {
          // 保留标签和颜色信息，只更新文本
          const preservedProperties = {
            tags: lines[index].tags,
            customTag: lines[index].customTag,
            tagColor: lines[index].tagColor
          };
          lines[index] = { ...preservedProperties, text: newText };
          // 更新codeTextMap中的文本
          this.codeTextMap[this.selectedFilePath] = lines.map(l => l.text).join('\n');
        }
      }
    },
    
    // 上传修改后的代码到后端进行重新分析
    async uploadModifiedCode() {
      if (!this.selectedFilePath) {
        this.toast('请选择一个文件');
        return;
      }
      
      const codeText = this.codeTextMap[this.selectedFilePath] || 
                      this.currentCode.map(l => l.text).join('\n');
      const codeId = this.selectedFilePath.split('/').pop() || 'modified_code.c';
      
      // 设置分析状态
      this.isAnalyzing = true;
      this.analysisProgress = 0;
      
      // 模拟分析进度
      const analysisInterval = setInterval(() => {
        if (this.analysisProgress < 90) {
          this.analysisProgress += 2;
        }
      }, 100);
      
      try {
        const ok = await this.analyze(codeId, codeText);
        clearInterval(analysisInterval);
        this.analysisProgress = 100;
        
        if (ok) {
          this.toast('代码已上传并重新分析');
        } else {
          this.toast('代码上传分析失败');
        }
      } catch (error) {
        clearInterval(analysisInterval);
        this.analysisProgress = 0;
        this.isAnalyzing = false;
        console.error('上传修改后代码时出错:', error);
        this.toast('上传修改后代码时出错');
      }
      
      // 任务完成后更新状态
      setTimeout(() => {
        this.isAnalyzing = false;
      }, 500);
    },
    
    // 管理员功能相关方法
    closeAdminPanel() {
      this.showAdminPanel = false;
    },
    
    deleteUserProjects(username) {
      // 删除指定用户的全部项目
      if (confirm(`确定要删除用户 ${username} 的所有项目吗？此操作不可恢复。`)) {
        // 这里应该调用后端API删除用户的所有项目
        console.log(`删除用户 ${username} 的所有项目`);
        
        // 前端模拟：更新本地数据
        const userIndex = this.adminUsers.findIndex(user => user.username === username);
        if (userIndex !== -1) {
          this.adminUsers[userIndex].projects = [];
          this.toast(`用户 ${username} 的项目已删除`);
        }
      }
    },
    
    deleteProjectById(username, projectId) {
      // 删除指定用户的特定项目
      if (confirm(`确定要删除项目吗？此操作不可恢复。`)) {
        // 这里应该调用后端API删除特定项目
        console.log(`删除用户 ${username} 的项目ID ${projectId}`);
        
        // 前端模拟：更新本地数据
        const userIndex = this.adminUsers.findIndex(user => user.username === username);
        if (userIndex !== -1) {
          const projectIndex = this.adminUsers[userIndex].projects.findIndex(p => p.id === projectId);
          if (projectIndex !== -1) {
            this.adminUsers[userIndex].projects.splice(projectIndex, 1);
            this.toast(`项目已删除`);
          }
        }
      }
    },
    
    // 获取所有用户及其项目信息
    async fetchAllUsersAndProjects() {
      try {
        // 这里应该调用后端API获取所有用户及其项目信息
        // const response = await fetch(`${this.apiBase}/Admin/getUsers`, {
        //   method: 'GET',
        //   headers: {
        //     'Content-Type': 'application/json',
        //   },
        // });
        // 
        // if (response.ok) {
        //   const data = await response.json();
        //   if (data.state === 'success') {
        //     this.adminUsers = data.rst;
        //   } else {
        //     throw new Error(data.description || '获取用户列表失败');
        //   }
        // } else {
        //   throw new Error('网络请求失败');
        // }
        
        // 模拟API调用成功
        this.toast('获取用户列表成功');
      } catch (error) {
        console.error('获取用户列表失败:', error);
        this.toast('获取用户列表失败: ' + error.message);
      }
    },
    
    // 统计类型改变时的处理
    onStatTypeChange() {
      // 这里可以根据选择的统计类型请求后端获取相应的统计数据
      // 例如，调用后端API获取特定类型的统计图表数据
      console.log('统计类型已更改为:', this.statType);
      
      // 清空之前的服务端数据，以便显示计算属性中的默认数据
      this.serverBarData = null;
      
      // 如果需要，可以调用后端API获取特定类型的统计图表数据
      // this.fetchStatData(this.statType);
    },
    
    // 请求后端获取指定类型的统计数据
    async fetchStatData(statType) {
      try {
        const base = (this.apiBase || '').replace(/\\+$/, '')
        const codeId = (this.selectedFilePath || '').split('/').pop() || ''
        
        // 构造请求参数
        const fd = new FormData()
        fd.append('userId', this.userId || 'demo')
        fd.append('codeId', codeId)
        fd.append('statType', statType)
        
        // 发送请求到后端获取统计图表数据
        const response = await fetch(`${base}/Analysis/statistics`, { 
          method: 'POST', 
          body: fd 
        })
        
        if (response.ok) {
          const data = await response.json()
          if (data.state === 'success' && data.rst) {
            // 更新统计数据显示
            this.updateStatChart(data.rst)
          } else {
            console.error('获取统计图表数据失败:', data.description)
          }
        } else {
          console.error('请求统计图表数据失败:', response.statusText)
        }
      } catch (error) {
        console.error('请求统计图表数据时发生错误:', error)
      }
    },
    
    // 更新统计图表显示
    updateStatChart(statData) {
      // 这里将后端返回的统计图表数据应用到前端显示
      // 具体实现取决于后端返回的数据格式
      console.log('收到统计图表数据:', statData)
      
      // 示例：如果后端返回的是类似barData格式的数据
      if (statData.barData) {
        // 可以将数据保存到组件中供barData计算属性使用
        this.serverBarData = statData.barData
      }
    },
  },
  mounted() {
    Prism.highlightAll()
    const savedTheme = localStorage.getItem('theme') || 'light'
    this.theme = savedTheme
    document.documentElement.setAttribute('data-theme', savedTheme)
    const savedConfig = JSON.parse(localStorage.getItem('config') || '{}')
    this.config = Object.assign(this.config, savedConfig)
    const savedCollapsed = JSON.parse(localStorage.getItem('collapsed') || '{}')
    this.leftCollapsed = !!savedCollapsed.left
    this.codeCollapsed = !!savedCollapsed.code
    this.chatOnly = !!savedCollapsed.chatOnly
    this.apiBase = localStorage.getItem('apiBase') || this.apiBase
    window.addEventListener('keydown', (e) => {
      // 检查事件目标是否是输入框或文本域，如果是则不执行快捷键功能
      const target = e.target;
      const isInputElement = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.contentEditable === 'true';
      
      if (e.ctrlKey && e.key === 'Enter') {
        if (!isInputElement) this.send();
      } else if (!e.ctrlKey && e.key.toLowerCase() === 'l') {
        if (!isInputElement) this.toggleLeft();
      } else if (!e.ctrlKey && e.key.toLowerCase() === 'p') {
        if (!isInputElement) this.toggleCode();
      } else if (e.key === 'Escape') {
        this.searchTextRaw = '';
      }
    })
    this.$watch('searchTextRaw', (val) => { clearTimeout(this._searchTimer); this._searchTimer = setTimeout(() => { this.searchText = val }, 200) })
    this.$watch('leftCollapsed', (val) => { const c = JSON.parse(localStorage.getItem('collapsed') || '{}'); c.left = !!val; localStorage.setItem('collapsed', JSON.stringify(c)) })
    this.$watch('codeCollapsed', (val) => { const c = JSON.parse(localStorage.getItem('collapsed') || '{}'); c.code = !!val; localStorage.setItem('collapsed', JSON.stringify(c)) })
    this.$watch('chatOnly', (val) => { const c = JSON.parse(localStorage.getItem('collapsed') || '{}'); c.chatOnly = !!val; localStorage.setItem('collapsed', JSON.stringify(c)) })
    
    // 设置定期获取状态信息的定时器
    this.statusInterval = setInterval(async () => {
      if (this.showStatusPanel) {
        await this.fetchCurrentStatus();
      }
    }, 2000); // 每2秒更新一次状态
  },
  beforeUnmount() {
    // 清理定时器
    if (this.statusInterval) {
      clearInterval(this.statusInterval);
    }
  },
  updated() { Prism.highlightAll() }
}
</script>
