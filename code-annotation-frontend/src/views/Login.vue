
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
        label="手机号"
        name="telphone"
        fieldDecoratorId
        :rules="[{ required: true, message: '请输入手机号！' }]"
      >
        <a-input v-model:value="formState.telphone" />
      </a-form-item>

      <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码！' }]">
        <a-input-password v-model:value="formState.password" />
      </a-form-item>

      <a-form-item name="login" :wrapper-col="{ offset: 8, span: 16 }">
        <a-button type="primary" html-type="submit" class="login-form-button" @click="handleLogin()"> 登录 </a-button>
        <a-button style="margin-left:8px" @click="enterAsGuest()">游客进入</a-button>
        Or
        <router-link to="../register">立即注册</router-link>
        <br />
        <router-link to="../modifypw">修改密码</router-link>
      </a-form-item>
    </a-form>
  </div>
  </template>
  <script>
  import { defineComponent, reactive } from "vue";
  import path from "@/api/path.js";
  import { postData } from "@/api/webpost";
  import { getData } from "@/api/webget";
  import { message } from "ant-design-vue";
  import { useRouter } from "vue-router";
  import HeaderNav from "@/components/HeaderNav.vue";
  export default defineComponent({
    components: { HeaderNav },
    setup() {
      const router = useRouter();
      const formState = reactive({ telphone: "", password: "" });
      const onFinish = (values) => { };
      const onFinishFailed = (errorInfo) => { };
      function handleLogin() {
        let params = new URLSearchParams();
        params.append("telphone", formState.telphone);
        params.append("password", formState.password);
        let url = path.website.login;
        postData(url, params).then((res) => {
          if (res.state === "success") {
            message.success(res.state);
            window.localStorage.setItem("userId", res.rst.username);
            if (res.rst.username === "admin") {
              router.push({ name: "alluser" });
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
  .container { display: flex; justify-content: center; align-items: center; min-height: 650px; background-size: cover; background: #eeeded; }
  .login-form { border-radius: 6px; background: #ffffff; width: 350px; padding: 25px 25px 5px 25px; }
  </style>
