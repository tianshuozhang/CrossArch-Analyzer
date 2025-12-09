
<template>
  <div class="menu">
    <div style="cursor: pointer">
      <div class="logo" @click="toIndex">Q</div>
    </div>
    <a-menu style="justify-content: flex-end" :selectedKeys="curPage" mode="horizontal" @click="changePage">
      <a-sub-menu key="person">
        <template #icon><UserOutlined /></template>
        <a-menu-item v-if="isVisitor" key="visitor"> 当前：游客 </a-menu-item>
        <a-menu-item v-if="!isVisitor"> 用户名：{{ userId }} </a-menu-item>
        <a-menu-item key="intro">
          <router-link to="../intro">功能介绍</router-link>
        </a-menu-item>
        <a-menu-item v-if="isVisitor" key="login">
          <router-link to="../login">登录</router-link>
        </a-menu-item>
        <a-menu-item v-if="isVisitor" key="register">
          <router-link to="../register">注册</router-link>
        </a-menu-item>
        <a-menu-item v-if="!isVisitor" key="modifypw">
          <router-link to="../modifypw">修改密码</router-link>
        </a-menu-item>
        <a-menu-item v-if="!isVisitor" key="remove">
          <router-link to="../remove">注销</router-link>
        </a-menu-item>
        <a-menu-item v-if="!isVisitor" key="exit" @click="handleExit()">退出</a-menu-item>
      </a-sub-menu>
    </a-menu>
  </div>
  </template>
  <script>
  import { defineComponent, ref } from "vue";
  import { UserOutlined } from "@ant-design/icons-vue";
  import { useRouter } from "vue-router";
  import path from "@/api/path.js";
  import { getData } from "@/api/webget";
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
      let curPage = [props.current || 'code'];
      function changePage(item) {
        router.push({ name: item.key });
      }
      function toIndex() {
        router.push({ name: "code" });
      }
      function handleExit() {
        const params = new URLSearchParams();
        const url = path.website.exit;
        getData(url, params).then((res) => {
          if (res.state === "success") {
            message.success(res.description);
            window.localStorage.removeItem("userId");
            isVisitor.value = true;
            router.push({ name: "login" });
          } else {
            message.error(res.description);
          }
        });
      }
      return { curPage, toIndex, changePage, userId, isVisitor, handleExit };
    },
  });
  </script>
  <style scoped>
  .menu { display: flex; align-items: center; justify-content: space-between; height: 70px; }
  .logo { margin: 10px 10px 10px 20px; height: 45px; width: 45px; border-radius: 8px; background: #333; color: #fff; display:flex; align-items:center; justify-content:center; font-weight:600; }
  </style>
