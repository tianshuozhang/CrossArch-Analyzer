let Ip = "/api/";

let path = {
  website: {
    register: Ip + "User/register",
    login: Ip + "User/login",
    exit: Ip + "User/exit",
    modifyPW: Ip + "User/modifyPassword",
    removeUser: Ip + "User/removeUser",
    getUserList: Ip + "Admin/getUsers",
    admin_removeUser: Ip + "Admin/removeUser",
    getCodeList: Ip + "Code/getCodes",
    getCode: Ip + "Code/getCode",
    addCode: Ip + "Code/addCode",
    removeCode: Ip + "Code/removeCode",
    modifyCodeID: Ip + "Code/modifyCodeID",
    modifyCode: Ip + "Code/modifyCode",
    getLabelMark: Ip + "Mark/getLabelMark",
    getUserMark: Ip + "Mark/getUserMark",
    addMark: Ip + "Mark/addMark",
    removeMark: Ip + "Mark/removeMark",
    getCodeMark: Ip + "Mark/getCodeMark",
    getLabelList: Ip + "UserLabel/getUser",
    getLabel: Ip + "UserLabel/getLabel",
    addLabel: Ip + "UserLabel/addLabel",
    removeLabel: Ip + "UserLabel/removeLabel",
    modifyLabelID: Ip + "UserLabel/modifyLabelID",
    modifyLabelIntro: Ip + "UserLabel/modifyLabelintro",
  },
  project: {
    // 项目管理相关API
    getProjectList: Ip + "Project/list",
    createProject: Ip + "Project/create",
    openProject: Ip + "Project/open",
    deleteProject: Ip + "Project/delete",
    renameProject: Ip + "Project/rename",
    uploadProject: Ip + "Project/upload",
    getProjectTree: Ip + "Project/tree",
    updateProject: Ip + "Project/update",
    // 状态相关API
    getStatus: Ip + "Status/get",
    getUploadProgress: Ip + "Status/upload",
    getAnalysisProgress: Ip + "Status/analysis",
  }
};
export default path;
