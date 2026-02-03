import api from '@/api/index.js';

function toForm(params) {
  const isFormData = typeof FormData !== 'undefined' && params instanceof FormData;
  const isUrlParams = typeof URLSearchParams !== 'undefined' && params instanceof URLSearchParams;
  if (isFormData || isUrlParams) return params;
  if (!params || typeof params !== 'object') {
    return null;
  }
  const up = new URLSearchParams();
  Object.keys(params).forEach(k => {
    const v = params[k];
    if (Array.isArray(v)) v.forEach(item => up.append(k, item));
    else if (v !== undefined && v !== null) up.append(k, v);
  });
  return up;
}

export function postData(url, params) {
  return new Promise(function (resolve, reject) {
    api.post(url, null, toForm(params),
      successRes => { resolve(successRes); },
      failureRes => { reject(failureRes); }
    )
  })
}
