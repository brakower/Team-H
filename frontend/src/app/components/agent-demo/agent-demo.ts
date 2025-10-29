import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Agent, ToolSchema, AgentTask, AgentResult } from '../../services/agent';

@Component({
  selector: 'app-agent-demo',
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-demo.html',
  styleUrl: './agent-demo.css',
})
export class AgentDemo implements OnInit {
  tools: ToolSchema[] = [];
  task: string = '';
  maxIterations: number = 10;
  result: AgentResult | null = null;
  isLoading: boolean = false;
  error: string = '';
  healthStatus: string = '';

  constructor(private agentService: Agent) {}

  ngOnInit() {
    this.loadTools();
    this.checkHealth();
  }

  loadTools() {
    this.agentService.getTools().subscribe({
      next: (tools) => {
        this.tools = tools;
      },
      error: (err) => {
        this.error = 'Failed to load tools: ' + err.message;
      }
    });
  }

  checkHealth() {
    this.agentService.healthCheck().subscribe({
      next: (health) => {
        this.healthStatus = health.status;
      },
      error: (err) => {
        this.healthStatus = 'unhealthy';
      }
    });
  }

  runTask() {
    if (!this.task) {
      this.error = 'Please enter a task';
      return;
    }

    this.isLoading = true;
    this.error = '';
    this.result = null;

    const agentTask: AgentTask = {
      task: this.task,
      max_iterations: this.maxIterations
    };

    this.agentService.runAgent(agentTask).subscribe({
      next: (result) => {
        this.result = result;
        this.isLoading = false;
      },
      error: (err) => {
        this.error = 'Failed to run task: ' + err.message;
        this.isLoading = false;
      }
    });
  }

  executeTool(toolName: string) {
    // Simple execution with empty parameters for demo
    this.agentService.executeTool({
      tool_name: toolName,
      parameters: {}
    }).subscribe({
      next: (result) => {
        console.log('Tool executed:', result);
      },
      error: (err) => {
        this.error = 'Failed to execute tool: ' + err.message;
      }
    });
  }
}

