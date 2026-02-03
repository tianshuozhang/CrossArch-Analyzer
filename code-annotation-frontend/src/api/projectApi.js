import { postData } from './webpost.js';
import { getData } from './webget.js';
import path from './path.js';

export const projectApi = {
  getProjectList: () => postData(path.project.getProjectList, {}),
  addProject: (formData) => postData(path.project.addProject, formData),
  uploadProject: (formData) => postData(path.project.uploadProject, formData),
  openProject: (project_id) => {
    const formData = new FormData();
    formData.append('project_id', project_id);
    return postData(path.project.openProject, formData);
  },
  deleteProject: (project_id) => {
    const formData = new FormData();
    formData.append('project_id', project_id);
    return postData(path.project.deleteProject, formData);
  },
  getProjectTree: (project_id) => getData(path.project.getProjectTree, { project_id }),
  closeProject: () => postData(path.project.closeProject, {}),
  openFile: (filePath) => {
    return postData(path.file.open, { file_path: filePath });
  },
  saveFile: (filePath, fileData) => {
    const formData = new FormData();
    formData.append('file_path', filePath);
    formData.append('file_data', JSON.stringify(fileData));
    return postData(path.file.save, formData);
  },
  cancelFile: (filePath) => {
    const formData = new FormData();
    formData.append('file_path', filePath);
    return postData(path.file.cancel, formData);
  },
  closeFile: (filePath, fileData) => {
    const formData = new FormData();
    formData.append('file_path', filePath);
    formData.append('file_data', JSON.stringify(fileData));
    return postData(path.file.close, formData);
  },
  startAnalysis: (project_id) => {
    const formData = new FormData();
    formData.append('project_id', project_id);
    return postData(path.analysis.start, formData);
  },
  getAnalysisProgress: (task_id) => getData(path.analysis.progress, { task_id }),
  cancelAnalysis: (task_id) => {
    const formData = new FormData();
    formData.append('task_id', task_id);
    return postData(path.analysis.cancel, formData);
  },
  fetchAnalysis: (file_path, project_id, task_id) => {
    const formData = new FormData();
    formData.append('file_path', file_path);
    formData.append('project_id', project_id);
    formData.append('task_id', task_id);
    return postData(path.analysis.fetch, formData);
  },
  getAnalysisReport: (project_id) => {
    const formData = new FormData();
    formData.append('project_id', project_id);
    return postData(path.analysis.report, formData);
  },
  askAnalysis: (question) => {
    const formData = new FormData();
    formData.append('question', question);
    return postData(path.analysis.ask, formData);
  },
  getGraphList: (project_id) => {
    const formData = new FormData();
    formData.append('project_id', project_id);
    return postData(path.graph.getList, formData);
  },
  getGraph: (graph_id) => {
    const formData = new FormData();
    formData.append('graph_id', graph_id);
    return postData(path.graph.getGraph, formData);
  },
  modifyArchTag: (file_path, line, remove_tag_text, arch_tag_text, arch_tag_color) => {
    const formData = new FormData();
    formData.append('file_path', file_path);
    formData.append('line', line);
    formData.append('remove_tag_text', remove_tag_text);
    formData.append('arch_tag_text', arch_tag_text);
    formData.append('arch_tag_color', arch_tag_color);
    return postData(path.archTag.modify, formData);
  }
};
