
<template>
  <div class="menu">
    <div style="cursor: pointer">
      <div class="logo" @click="toIndex">Q</div>
    </div>
    <a-menu style="justify-content: flex-end" :selectedKeys="curPage" mode="horizontal" @click="changePage">
      <a-sub-menu key="person">
        <template #icon><UserOutlined /></template>
        <a-menu-item v-if="isVisitor" key="visitor">游客</a-menu-item>
        <a-menu-item v-if="!isVisitor">{{ userId }}</a-menu-item>
        <a-menu-item v-if="isVisitor" key="login" @click="showLoginModal = true">
          登录
        </a-menu-item>
        <a-menu-item v-if="isVisitor" key="register" @click="showRegisterModal = true">
          注册
        </a-menu-item>
        <a-menu-item v-if="!isVisitor && userId !== 'admin'">
          <router-link to="../modifypw">修改密码</router-link>
        </a-menu-item>
        <a-menu-item v-if="userId === 'admin'" key="admin-projects">
          <router-link to="../admin-projects">管理面板</router-link>
        </a-menu-item>
        <a-menu-item v-if="!isVisitor" key="remove">
          <router-link to="../remove">注销</router-link>
        </a-menu-item>
        <a-menu-item v-if="!isVisitor" key="exit" @click="handleExit()">退出</a-menu-item>
      </a-sub-menu>
    </a-menu>
    
    <!-- 登录弹窗 -->
    <div v-if="showLoginModal" class="modal-overlay" @click="closeLoginModal">
      <div class="login-modal" @click.stop>
        <div class="modal-header">
          <h3>用户登录</h3>
          <button class="modal-close" @click="closeLoginModal">×</button>
        </div>
        <div class="modal-body">
          <div class="login-form-group">
            <label>用户名</label>
            <input v-model="loginForm.username" type="text" placeholder="请输入用户名" class="login-input" />
          </div>
          <div class="login-form-group">
            <label>密码</label>
            <input v-model="loginForm.password" type="password" placeholder="请输入密码" class="login-input" />
          </div>
          <div class="login-buttons">
            <button @click="handleLogin" class="btn primary">登录</button>
            <button @click="loginAsGuest" class="btn secondary">游客进入</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 注册弹窗 -->
    <div v-if="showRegisterModal" class="modal-overlay" @click="closeRegisterModal">
      <div class="login-modal" @click.stop>
        <div class="modal-header">
          <h3>用户注册</h3>
          <button class="modal-close" @click="closeRegisterModal">×</button>
        </div>
        <div class="modal-body">
          <div class="login-form-group">
            <label>用户名</label>
            <input v-model="registerForm.username" type="text" placeholder="请输入用户名" class="login-input" />
          </div>
          <div class="login-form-group">
            <label>密码</label>
            <input v-model="registerForm.password" type="password" placeholder="请输入密码" class="login-input" />
          </div>
          <div class="login-form-group">
            <label>确认密码</label>
            <input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" class="login-input" />
          </div>
          <div class="login-buttons">
            <button @click="handleRegister" class="btn primary">注册</button>
            <button @click="closeRegisterModal" class="btn secondary">取消</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
  import { defineComponent, ref, reactive } from "vue";
  import { UserOutlined } from "@ant-design/icons-vue";
  import { useRouter } from "vue-router";
  import path from "@/api/path.js";
  import { getData } from "@/api/webget";
  import { postData } from "@/api/webpost";
  import message from "ant-design-vue/es/message";
  export default defineComponent({
    props: {
      current: String,
    },
    components: {
      UserOutlined,
    },
    setup(props) {
      const router = useRouter();
      const userId = window.localStorage.getItem("userId");
      const isVisitor = ref(userId === null || userId === 'demo');
      
      // 弹窗控制
      const showLoginModal = ref(false);
      const showRegisterModal = ref(false);
      
      // 登录表单数据
      const loginForm = reactive({
        username: '',
        password: ''
      });
      
      // 注册表单数据
      const registerForm = reactive({
        username: '',
        password: '',
        confirmPassword: ''
      });
      
      let curPage = [props.current || 'code'];
      
      function changePage(item) {
        router.push({ name: item.key });
      }
      
      function toIndex() {
        router.push({ name: "code" });
      }
      
      // 显示/关闭登录弹窗
      function closeLoginModal() {
        showLoginModal.value = false;
        // 清空表单
        loginForm.username = '';
        loginForm.password = '';
      }
      
      // 显示/关闭注册弹窗
      function closeRegisterModal() {
        showRegisterModal.value = false;
        // 清空表单
        registerForm.username = '';
        registerForm.password = '';
        registerForm.confirmPassword = '';
      }
      
      // 处理登录
      function handleLogin() {
        router.push({ name: 'login' });
      }
      
      // 处理注册

      function handleRegister() {
        router.push({ name: 'login' });

      }
      
      // 游客登录
      function loginAsGuest() {
        window.localStorage.setItem('userId','demo');
        isVisitor.value = true;  // 游客登录后仍应保持isVisitor为true
        closeLoginModal();
        router.push({ name: 'code' });
      }
      
      function handleExit() {
        const params = new URLSearchParams();
        const url = path.website.exit;
        getData(url, params).then((res) => {
          if (res.state === "success") {
            message.success(res.description);
            window.localStorage.removeItem("userId");
            isVisitor.value = true;
            router.push({ name: "code" });
          } else {
            message.error(res.description);
          }
        }).catch(error => {
          // 如果退出接口调用失败（比如对于游客用户），也要清除本地存储并设置为访客状态
          window.localStorage.removeItem("userId");
          isVisitor.value = true;
          router.push({ name: "code" });
        });
      }
      
      return { 
        curPage, 
        toIndex, 
        changePage, 
        userId, 
        isVisitor, 
        handleExit,
        showLoginModal,
        showRegisterModal,
        loginForm,
        registerForm,
        closeLoginModal,
        closeRegisterModal,
        handleLogin,
        handleRegister,
        loginAsGuest
      };
    },
  });
</script>
<style scoped>
.menu { display: flex; align-items: center; justify-content: space-between; height: 70px; }
.logo { margin: 10px 10px 10px 20px; height: 45px; width: 45px; border-radius: 8px; background: #333; color: #fff; display:flex; align-items:center; justify-content:center; font-weight:600; }

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.login-modal {
  background: white;
  border-radius: 8px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 10px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: #333;
  background: #f5f5f5;
  border-radius: 50%;
}

.modal-body {
  padding: 20px;
}

.login-form-group {
  margin-bottom: 15px;
}

.login-form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.login-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.login-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.login-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.login-buttons .btn {
  flex: 1;
  padding: 8px 16px;
  text-align: center;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.btn.primary {
  background: #1890ff;
  color: white;
}

.btn.primary:hover {
  background: #40a9ff;
}

.btn.secondary {
  background: #f0f0f0;
  color: #333;
}

.btn.secondary:hover {
  background: #e0e0e0;
}
</style>
