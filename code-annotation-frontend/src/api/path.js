let Ip = "/api/";
let path = {
  website: {
    register: Ip + "User/register",
    login: Ip + "User/login",
    modifyPW: Ip + "User/modify_password"
  },
  project: {
    getProjectList: Ip + "Project/get_project_list",
    addProject: Ip + "Project/add",
    openProject: Ip + "Project/open",
    deleteProject: Ip + "Project/delete",
    uploadProject: Ip + "Project/upload",
    getProjectTree: Ip + "Project/get_tree",
    closeProject: Ip + "Project/close"
  },
  file: {
    open: Ip + "File/open",
    save: Ip + "File/save",
    cancel: Ip + "File/cancel",
    close: Ip + "File/close"
  },
  analysis: {
    cancel: Ip + "Analysis/cancel",
    progress: Ip + "Analysis/progress",
    ask: Ip + "Analysis/ask",
    fetch: Ip + "Analysis/fetch",
    start: Ip + "Analysis/analysis",
    report: Ip + "Analysis/report"
  },
  graph: {
    getList: Ip + "Graph/get_list",
    getGraph: Ip + "Graph/get_graph"
  },
  archTag: {
    modify: Ip + "ArchTag/modify"
  }
};
export default path;
