<template>
  <header-nav :current="'admin-projects'"></header-nav>
  <div class="app" :style="{gridTemplateColumns: '320px 1fr 320px'}">
    <header class="topbar">
      <div class="brand">
        <div class="logo">Q</div>
        <div class="title">管理员 - 用户项目管理</div>
      </div>
      <div class="top-actions">
        <button class="btn ghost" @click="toggleLeft">{{ leftCollapsed? '▸ 展开左侧':'▾ 收起左侧' }}</button>
        <button class="btn ghost" @click="toggleCode">{{ codeCollapsed? '▸ 展开预览':'▾ 收起预览' }}</button>
        <button class="btn ghost" @click="toggleChatOnly">{{ chatOnly? '全布局':'仅对话' }}</button>
        <button class="btn ghost" @click="toggleTheme">{{ theme==='light'?'🌙 暗色':'☀️ 亮色' }}</button>
      </div>
    </header>

    <aside class="left" v-show="!leftCollapsed">
      <div class="panel-title strong">
        <span>功能区</span>
        <button class="icon-btn" @click="toggleLeft">{{ leftCollapsed? '▸ 展开左侧':'▾ 收起左侧' }}</button>
      </div>
      <section class="panel">
        <div class="panel-title">项目管理</div>
        <div class="project-controls">
          <button class="btn primary" @click="loadUserData">刷新用户数据</button>
        </div>
      </section>
      <section class="panel">
        <div class="panel-title">管理员功能</div>
        <div class="project-controls">
          <button class="btn secondary" @click="showAdminPanel = true">查看用户项目</button>
        </div>
      </section>
    </aside>

    <main class="center">
      <section class="code" v-show="!codeCollapsed">
        <div class="code-toolbar">
          <div class="tools">
            <button class="icon-btn" @click="toggleCode">{{ codeCollapsed? '▸ 展开预览':'▾ 收起预览' }}</button>
          </div>
        </div>
        <div class="code-view" style="padding: 20px; overflow-y: auto;">
          <h2>管理员控制台</h2>
          <p>欢迎使用管理员功能。您可以查看所有用户及其项目信息。</p>
          
          <div class="admin-stats" v-if="users.length > 0">
            <h3>系统统计</h3>
            <ul>
              <li>总用户数: {{ users.length }}</li>
              <li>总项目数: {{ totalProjects }}</li>
            </ul>
          </div>
          
          <div class="user-list" v-if="users.length > 0">
            <h3>用户列表</h3>
            <div v-for="user in users" :key="user.username" class="user-card">
              <div class="user-header" @click="toggleUserDetails(user.username)">
                <h4>用户: {{ user.username }}</h4>
                <span class="toggle-icon">{{ expandedUsers[user.username] ? '▼' : '▶' }}</span>
              </div>
              
              <div v-if="expandedUsers[user.username]" class="user-details">
                <div class="user-info">
                  <p>手机号: {{ user.telphone }}</p>
                  <p>代码文件数: {{ user.numFile }}</p>
                  <p>标签数: {{ user.numTag }}</p>
                  <p>标注关系数: {{ user.numRelation }}</p>
                </div>
                
                <div class="user-projects" v-if="user.projects && user.projects.length > 0">
                  <h5>项目列表</h5>
                  <div v-for="project in user.projects" :key="project.id" class="project-item">
                    <div class="project-info">
                      <span>{{ project.name }}</span>
                      <small style="color: #999; margin-left: 10px;">路径: {{ project.path }}</small>
                    </div>
                    <div class="project-actions">
                      <button class="btn danger small" @click="deleteProject(user.username, project.id)">删除</button>
                    </div>
                  </div>
                </div>
                <div v-else class="no-projects">
                  <p>该用户暂无项目</p>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="no-users">
            <p>暂无用户数据</p>
          </div>
        </div>
      </section>
    </main>

    <aside class="right" v-show="chatOnly || !codeCollapsed">
      <section class="panel">
        <div class="panel-title strong">
          <span>系统日志</span>
        </div>
        <div class="log-content">
          <div v-for="log in logs" :key="log.id" class="log-item">{{ log.message }}</div>
        </div>
      </section>
    </aside>
    
    <!-- 管理员功能弹窗 -->
    <div class="overlay" v-if="showAdminPanel" @click="closeAdminPanel"></div>
    <div class="status-info-panel" v-if="showAdminPanel" @click.stop style="min-width: 500px; max-width: 800px;">
      <h3>管理员控制面板</h3>
      <div style="margin: 15px 0;">
        <h4>用户项目管理</h4>
        <div v-if="users.length > 0">
          <div v-for="user in users" :key="user.username" class="admin-user-item">
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; border: 1px solid #eee; margin-bottom: 5px; border-radius: 4px;">
              <span>{{ user.username }} (项目数: {{ user.projects?.length || 0 }})</span>
              <button class="btn danger small" @click="removeUser(user.username)">删除用户</button>
            </div>
          </div>
        </div>
        <div v-else>
          <p>暂无用户数据</p>
        </div>
      </div>
      <div style="text-align: right; margin-top: 15px;">
        <button class="btn secondary" @click="closeAdminPanel">关闭</button>
      </div>
    </div>
    
    <!-- 删除项目确认弹窗 -->
    <div v-if="showDeleteConfirm" class="overlay" @click="hideDeleteConfirm"></div>
    <div v-if="showDeleteConfirm" class="confirm-modal" @click.stop>
      <div class="modal-content">
        <h3>确认删除项目</h3>
        <p>确定要删除用户 "{{ deleteUser }}" 的项目 "{{ deleteProjectName }}" 吗？</p>
        <div class="modal-actions">
          <button class="btn secondary" @click="hideDeleteConfirm">取消</button>
          <button class="btn danger" @click="confirmDeleteProject">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, reactive } from "vue";
import HeaderNav from "@/components/HeaderNav.vue";
import { getData } from "@/api/webget";
import { postData } from "@/api/webpost";
import path from "@/api/path.js";
import message from "ant-design-vue/es/message";

export default defineComponent({
  components: { HeaderNav },
  setup() {
    // 模拟用户数据
    const users = ref([
      {
        username: "admin",
        telphone: "13800138000",
        numFile: 5,
        numTag: 10,
        numRelation: 3,
        projects: [
          { id: 1, name: "管理系统项目", path: "/projects/admin_system" },
          { id: 2, name: "数据分析项目", path: "/projects/data_analysis" }
        ]
      },
      {
        username: "user1",
        telphone: "13800138001",
        numFile: 3,
        numTag: 5,
        numRelation: 2,
        projects: [
          { id: 3, name: "前端项目", path: "/projects/frontend_dev" }
        ]
      },
      {
        username: "user2",
        telphone: "13800138002",
        numFile: 7,
        numTag: 15,
        numRelation: 8,
        projects: [
          { id: 4, name: "后端项目", path: "/projects/backend_dev" },
          { id: 5, name: "API项目", path: "/projects/api_project" },
          { id: 6, name: "测试项目", path: "/projects/test_project" }
        ]
      }
    ]);
    
    const expandedUsers = reactive({});
    const showAdminPanel = ref(false);
    const showDeleteConfirm = ref(false);
    const deleteUser = ref('');
    const deleteProjectId = ref('');
    const deleteProjectName = ref('');
    const logs = ref([
      { id: 1, message: "系统启动" },
      { id: 2, message: "加载用户数据" },
      { id: 3, message: "管理员登录" }
    ]);
    
    // UI 控制
    const leftCollapsed = ref(false);
    const codeCollapsed = ref(false);
    const chatOnly = ref(false);
    const theme = ref('light');
    
    // 计算总项目数
    const totalProjects = computed(() => {
      return users.value.reduce((total, user) => total + (user.projects?.length || 0), 0);
    });
    
    // 切换用户详情显示/隐藏
    function toggleUserDetails(username) {
      expandedUsers[username] = !expandedUsers[username];
    }
    
    // 加载用户数据
    function loadUserData() {
      // 模拟加载数据
      message.info('刷新用户数据...');
      // 实际应用中这里会调用API
    }
    
    // 删除项目
    function deleteProject(username, projectId) {
      deleteUser.value = username;
      deleteProjectId.value = projectId;
      // 查找项目名称
      const user = users.value.find(u => u.username === username);
      if (user) {
        const project = user.projects.find(p => p.id === projectId);
        if (project) {
          deleteProjectName.value = project.name;
        }
      }
      showDeleteConfirm.value = true;
    }
    
    // 确认删除项目
    function confirmDeleteProject() {
      // 从用户项目列表中移除项目
      const user = users.value.find(u => u.username === deleteUser.value);
      if (user && user.projects) {
        user.projects = user.projects.filter(p => p.id !== deleteProjectId.value);
        message.success(`项目 "${deleteProjectName.value}" 已删除`);
        logs.value.unshift({ id: Date.now(), message: `删除了用户 ${deleteUser.value} 的项目 ${deleteProjectName.value}` });
      }
      
      hideDeleteConfirm();
    }
    
    // 隐藏删除确认弹窗
    function hideDeleteConfirm() {
      showDeleteConfirm.value = false;
      deleteUser.value = '';
      deleteProjectId.value = '';
      deleteProjectName.value = '';
    }
    
    // 删除用户
    function removeUser(username) {
      if (confirm(`确定要删除用户 "${username}" 吗？此操作不可逆。`)) {
        // 从用户列表中移除用户
        const index = users.value.findIndex(u => u.username === username);
        if (index !== -1) {
          users.value.splice(index, 1);
          message.success(`用户 "${username}" 已删除`);
          logs.value.unshift({ id: Date.now(), message: `删除了用户 ${username}` });
        }
      }
    }
    
    // 关闭管理员面板
    function closeAdminPanel() {
      showAdminPanel.value = false;
    }
    
    // UI 控制函数
    function toggleLeft() {
      leftCollapsed.value = !leftCollapsed.value;
    }
    
    function toggleCode() {
      codeCollapsed.value = !codeCollapsed.value;
    }
    
    function toggleChatOnly() {
      chatOnly.value = !chatOnly.value;
    }
    
    function toggleTheme() {
      theme.value = theme.value === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', theme.value);
    }
    
    return {
      users,
      expandedUsers,
      showAdminPanel,
      showDeleteConfirm,
      deleteUser,
      deleteProjectId,
      deleteProjectName,
      logs,
      leftCollapsed,
      codeCollapsed,
      chatOnly,
      theme,
      totalProjects,
      toggleUserDetails,
      loadUserData,
      deleteProject,
      confirmDeleteProject,
      hideDeleteConfirm,
      removeUser,
      closeAdminPanel,
      toggleLeft,
      toggleCode,
      toggleChatOnly,
      toggleTheme
    };
  },
  computed: {
    totalProjects() {
      return this.users.reduce((total, user) => total + (user.projects?.length || 0), 0);
    }
  }
});
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 320px 1fr 320px;
  grid-template-rows: auto 1fr;
  background: #f5f5f5;
}

header.topbar {
  grid-column: 1 / -1;
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

.brand {
  display: flex;
  align-items: center;
  gap: 15px;
}

.logo {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  background: #333;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.title {
  font-size: 18px;
  font-weight: 500;
  color: #333;
}

.top-actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn:hover {
  border-color: #40a9ff;
  color: #40a9ff;
}

.btn.primary {
  background: #1890ff;
  color: white;
  border-color: #1890ff;
}

.btn.primary:hover {
  background: #40a9ff;
  border-color: #40a9ff;
}

.btn.secondary {
  background: #f0f0f0;
  color: #333;
  border-color: #d9d9d9;
}

.btn.secondary:hover {
  background: #e6e6e6;
}

.btn.danger {
  background: #ff4d4f;
  color: white;
  border-color: #ff4d4f;
}

.btn.danger:hover {
  background: #ff7875;
  border-color: #ff7875;
}

.btn.ghost {
  background: transparent;
  border: 1px solid transparent;
  color: #666;
}

.btn.ghost:hover {
  background: #f5f5f5;
  border-color: #d9d9d9;
}

.btn.small {
  padding: 4px 8px;
  font-size: 12px;
}

.left {
  grid-row: 2;
  background: white;
  border-right: 1px solid #e8e8e8;
  overflow-y: auto;
  padding: 20px;
}

.center {
  grid-row: 2;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.right {
  grid-row: 2;
  background: white;
  border-left: 1px solid #e8e8e8;
  overflow-y: auto;
  padding: 20px;
}

.code {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.code-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.tools {
  display: flex;
  gap: 10px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d9d9d9;
  background: white;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
}

.icon-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.code-view {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.strong {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 0;
}

.project-controls .btn {
  width: 100%;
  margin-bottom: 0;
}

.panel {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.admin-stats {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
}

.admin-stats ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.admin-stats li {
  padding: 5px 0;
}

.user-card {
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 10px;
  overflow: hidden;
}

.user-header {
  background: #f8f9fa;
  padding: 12px 15px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-header:hover {
  background: #e9ecef;
}

.user-header h4 {
  margin: 0;
  font-size: 16px;
}

.toggle-icon {
  font-size: 12px;
}

.user-details {
  padding: 15px;
  background: #fff;
}

.user-info {
  margin-bottom: 15px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.user-info p {
  margin: 5px 0;
  font-size: 14px;
  color: #555;
}

.user-projects {
  margin-top: 15px;
}

.user-projects h5 {
  margin: 0 0 10px 0;
  padding-bottom: 5px;
  border-bottom: 1px solid #eee;
}

.project-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 5px;
  background: #f9f9f9;
}

.project-info {
  flex: 1;
}

.project-actions {
  display: flex;
  gap: 5px;
}

.no-projects, .no-users {
  padding: 15px;
  text-align: center;
  color: #999;
}

.log-content {
  max-height: 300px;
  overflow-y: auto;
}

.log-item {
  padding: 5px 0;
  border-bottom: 1px solid #eee;
  font-size: 12px;
  color: #666;
}

.admin-user-item {
  margin-bottom: 10px;
}

/* 重用Preview.vue中的样式 */
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
  max-height: 80vh;
  overflow-y: auto;
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

.confirm-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 8px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 1001;
  padding: 20px;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 15px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
</style>