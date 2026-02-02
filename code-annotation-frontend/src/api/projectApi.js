import { postData } from './webpost.js';
import { getData } from './webget.js';
import path from './path.js';

// 项目管理相关API
export const projectApi = {
  // 获取项目列表
  getProjectList: (params) => getData(path.project.getProjectList, params),
  
  // 创建项目
  createProject: (params) => postData(path.project.createProject, params),
  
  // 打开项目
  openProject: (params) => postData(path.project.openProject, params),
  
  // 删除项目
  deleteProject: (params) => postData(path.project.deleteProject, params),
  
  // 重命名项目
  renameProject: (params) => postData(path.project.renameProject, params),
  
  // 上传项目
  uploadProject: (params) => postData(path.project.uploadProject, params),
  
  // 获取项目目录树
  getProjectTree: (params) => getData(path.project.getProjectTree, params),
  
  // 更新项目
  updateProject: (params) => postData(path.project.updateProject, params),
  
  // 获取状态
  getStatus: (params) => getData(path.project.getStatus, params),
  
  // 获取上传进度
  getUploadProgress: (params) => getData(path.project.getUploadProgress, params),
  
  // 获取分析进度
  getAnalysisProgress: (params) => getData(path.project.getAnalysisProgress, params)
};