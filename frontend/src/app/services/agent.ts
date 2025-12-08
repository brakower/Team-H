import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { RubricItem } from "../models/rubric-item";

export interface ToolSchema {
  name: string;
  description: string;
  parameters: any;
}

export interface AgentTask {
  task: string;
  context: any;
  max_iterations?: number;
}

export interface AgentResult {
  result: any;
  log: string;
  steps: any[];
}

export interface ToolExecution {
  tool_name: string;
  parameters: any;
}

export interface ToolResult {
  tool: string;
  result: any;
}

@Injectable({
  providedIn: 'root'
})
export class Agent {
  private apiUrl = 'http://localhost:8000';
  constructor(private http: HttpClient) { }

  getTools(): Observable<ToolSchema[]> {
    return this.http.get<ToolSchema[]>(`${this.apiUrl}/tools`);
  }

  getToolSchema(toolName: string): Observable<ToolSchema> {
    return this.http.get<ToolSchema>(`${this.apiUrl}/tools/${toolName}`);
  }

  runAgent(task: AgentTask): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/run`, task);
  }  

  executeTool(execution: ToolExecution): Observable<ToolResult> {
    return this.http.post<ToolResult>(`${this.apiUrl}/execute`, execution);
  }

  discoverTools(): Observable<any> {
    return this.http.get(`${this.apiUrl}/discover`);
  }

  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  uploadFile(file: File): Observable<any> {
    const formData = new FormData();
    formData.append("file", file);
    return this.http.post<File>(`${this.apiUrl}/upload`, formData);
  }

  uploadGithubRepo(url: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/upload-github`, { url });
  }
}

