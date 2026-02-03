
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
      <a-form-item
        label="用户名"
        name="username"
        fieldDecoratorId
        :rules="[{ required: true, message: '请输入用户名！' }]"
      >
        <a-input v-model:value="formState.username" />
      </a-form-item>

      <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码！' }]">
        <a-input-password v-model:value="formState.password" />
      </a-form-item>

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
        let url = path.website.login;
        postData(url, { username: formState.username, password: formState.password }).then((res) => {
          if (res.state === "success") {
            message.success(res.description);
            window.localStorage.setItem("userId", res.rst.username || formState.username);
            if (res.rst && res.rst.token) {
              window.localStorage.setItem("token", res.rst.token);
            }
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
  min-height: 650px;
  background-size: cover;
  background: #eeeded;
}
.login-form {
  border-radius: 6px;
  background: #ffffff;
  width: 450px;
  padding: 25px 25px 5px 25px;
}
.login-links {
  text-align: center;
  margin-top: 12px;
}
</style>
