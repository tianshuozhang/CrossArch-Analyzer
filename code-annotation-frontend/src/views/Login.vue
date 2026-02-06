
<template>
  <header-nav></header-nav>
  <div class="container">
    <a-form
      :model="formState"
      name="basic"
      :label-col="{ span: 8 }"
      :wrapper-col="{ span: 16 }"
      autocomplete="off"
      @finish="onFinish"
      @finishFailed="onFinishFailed"
      class="login-form"
    >
      <h1 style="text-align: center">登录</h1>
      
      <div class="login-form-group">
        <label>用户名</label>
            <input v-model="formState.username" type="text" placeholder="请输入用户名" class="login-input" />
      </div>

      <div class="login-form-group">
        <label>密码</label>
            <input v-model="formState.password" type="password" placeholder="请输入密码" class="login-input" />
      </div>

      <a-form-item name="login" :wrapper-col="{ span: 24 }" style="text-align: center;">
        <a-button type="primary" html-type="submit" class="login-form-button" @click="handleLogin()" size="large" style="min-width: 120px; margin-right: 10px;"> 登录 </a-button>
        <a-button @click="enterAsGuest()" size="large" ghost style="min-width: 120px;">游客进入</a-button>
      </a-form-item>
      <div class="login-links">
        <router-link to="../register">立即注册</router-link>
        |
        <router-link to="../modifypw">修改密码</router-link>
      </div>
    </a-form>
  </div>
</template>
<script>
  import { defineComponent, reactive } from "vue";
  import path from "@/api/path.js";
  import { postData } from "@/api/webpost";
  import { getData } from "@/api/webget";
  import message from "ant-design-vue/es/message";
  import { useRouter } from "vue-router";
  import HeaderNav from "@/components/HeaderNav.vue";
  export default defineComponent({
    components: { HeaderNav },
    setup() {
      const router = useRouter();
      const formState = reactive({ username: "", password: "" });
      const onFinish = (values) => { };
      const onFinishFailed = (errorInfo) => { };
      function handleLogin() {
        let params = new URLSearchParams();
        params.append("username", formState.username);
        params.append("password", formState.password);
        let url = path.website.login;
        postData(url, params).then((res) => {
          if (res.state === "success") {
            message.success(res.description);
            // 存储用户名而不是硬编码'demo'
            window.localStorage.setItem("userId", formState.username);
            if (formState.username === "admin") {
              router.push({ name: "admin-projects" });
            } else {
              router.push({ name: "code" });
            }
          } else {
            message.error(res.description);
          }
        });
      }
      function enterAsGuest(){
        window.localStorage.setItem('userId','demo')
        router.push({ name: 'code' })
      }
      return { formState, onFinish, onFinishFailed, handleLogin, enterAsGuest };
    },
  });
</script>
<style scoped>
  .container { 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    min-height: 80vh; 
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 20px;
  }
  .login-form { 
    border-radius: 12px; 
    background: #ffffff; 
    width: 400px; 
    padding: 30px 30px 20px 30px; 
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.2);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255, 255, 255, 0.18);
  }
  .login-form h1 {
    color: #2c3e50;
    margin-bottom: 25px;
    text-align: center;
    font-weight: 600;
  }
  .login-form-button {
    width: 100%;
    margin-bottom: 10px;
  }
  .ant-form-item {
    margin-bottom: 16px;
  }
  .login-links {
    text-align: center;
    margin-top: 15px;
  }
  .login-links a {
    color: #3498db;
    margin: 0 8px;
  }
  .login-links a:hover {
    color: #2980b9;
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

</style>
