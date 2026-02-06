<template>
  <header-nav></header-nav>
  <div class="container">
    <a-form
      :model="formState"
      v-bind="layout"
      name="nest-messages"
      :validate-messages="validateMessages"
      @finish="onFinish"
      class="login-form"
    >
      <h1 style="text-align: center">注册</h1>
      <div class="login-form-group">
        <label>用户名</label>
        <input
          v-model="formState.user.name"
          type="text"
          placeholder="请输入用户名"
          class="login-input"
        />
      </div>

      <div class="login-form-group">
        <label>手机号</label>
        <input
          v-model="formState.user.telphone"
          type="text"
          placeholder="请输入手机号"
          class="login-input"
        />
      </div>

      <div class="login-form-group">
        <label>账号</label>
        <input
          v-model="formState.user.username"
          type="text"
          placeholder="请输入账号"
          class="login-input"
        />
      </div>

      <div class="login-form-group">
        <label>密码</label>
        <input
          v-model="formState.user.password"
          type="password"
          placeholder="请输入密码"
          class="login-input"
        />
      </div>

      <div class="login-form-group">
        <label>再次输入密码</label>
        <input
          v-model="formState.user.password_again"
          type="password"
          placeholder="请再次输入密码"
          class="login-input"
        />
      </div>


      <a-form-item :wrapper-col="{ offset: 8, span: 16 }">
        <a-button type="primary" html-type="submit" @click="handleRegister()">注册</a-button>
        <br />
        <router-link to="../login">已有账号？点我登录</router-link>
      </a-form-item>
    </a-form>
  </div>
</template>

<script>
import { defineComponent, reactive } from "vue";
import path from "@/api/path.js";
import { postData } from "@/api/webpost";
import { message } from "ant-design-vue";
import { useRouter } from "vue-router";
import HeaderNav from "@/components/HeaderNav.vue";

export default defineComponent({
  components: {
    HeaderNav,
  },
  setup() {
    const router = useRouter();

    const layout = {
      labelCol: {
        span: 8,
      },
      wrapperCol: {
        span: 16,
      },
    };
    const validateMessages = {
      required: "${label} is required!",
      types: {
        email: "${label} is not a valid email!",
        number: "${label} is not a valid number!",
      },
      number: {
        range: "${label} must be between ${min} and ${max}",
      },
    };
    const formState = reactive({
      user: {
        name: "",
        username: "",
        telphone: "",
        password: "",
        password_again: "",
      },
    });
    const onFinish = (values) => {
      console.log("Success:", values);
    };
    function handleRegister() {
      let params = new URLSearchParams();
      params.append("username", formState.user.username);
      params.append("telphone", formState.user.telphone);
      params.append("password", formState.user.password);
      params.append("password_again", formState.user.password_again);
      let url = path.website.register;
      postData(url, params).then((res) => {
        console.log(res);
        if (res.state === "success") {
          message.success(res.description);
          router.push({
            name: "login",
          });
        } else {
          message.error(res.description);
        }
      });
    }
    return {
      formState,
      onFinish,
      layout,
      validateMessages,
      handleRegister,
    };
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
</style>
