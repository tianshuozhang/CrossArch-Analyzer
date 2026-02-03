import axios from "axios";
axios.defaults.withCredentials = true;

function toType(obj) {
  return {}.toString.call(obj).match(/\s([a-zA-Z]+)/)[1].toLowerCase();
}

function filterNull(o) {
  for (var key in o) {
    if (o[key] === null) {
      delete o[key];
    }
    if (toType(o[key]) === "string") {
      o[key] = o[key].trim();
    } else if (toType(o[key]) === "object") {
      o[key] = filterNull(o[key]);
    } else if (toType(o[key]) === "array") {
      o[key] = filterNull(o[key]);
    }
  }
  return o;
}

function applyToken() {
  const t = typeof window !== "undefined" ? window.localStorage.getItem("token") : null;
  if (t) {
    axios.defaults.headers.common["Authorization"] = "Bearer " + t;
  }
}

function apiAxios(method, url, headers, params, success, failure) {
  applyToken();
  if (params) {
    // 检查 params 是否是 FormData 或 URLSearchParams 对象，如果是，就不处理
    const isFormData = typeof FormData !== 'undefined' && params instanceof FormData;
    const isUrlParams = typeof URLSearchParams !== 'undefined' && params instanceof URLSearchParams;
    if (!isFormData && !isUrlParams) {
      params = filterNull(params);
    }
  }
  axios({
    method: method,
    url: url,
    data: method === "POST" || method === "PUT" ? params : null,
    params: method === "GET" || method === "DELETE" ? params : null,
    withCredentials: false,
    crossDomain: true,
  })
    .then(function (res) {
      if (res.data) {
        if (success) { success(res.data); }
      } else {
        if (failure) failure(res.data);
      }
    })
    .catch(function (err) {
      let res = err.response;
      if (err) {
        window.alert("api error, HTTP CODE: " + (res && res.status));
      }
    });
}

export default {
  get: function (url, headers, params, success, failure) {
    return apiAxios("GET", url, headers, params, success, failure);
  },
  post: function (url, headers, params, success, failure) {
    return apiAxios("POST", url, headers, params, success, failure);
  },
  put: function (url, headers, params, success, failure) {
    return apiAxios("PUT", url, headers, params, success, failure);
  },
  delete: function (url, headers, params, success, failure) {
    return apiAxios("DELETE", url, headers, params, success, failure);
  },
};
