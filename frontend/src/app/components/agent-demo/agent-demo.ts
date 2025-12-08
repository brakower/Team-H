import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Agent, ToolSchema, AgentTask } from '../../services/agent';
import { RubricItem } from '../../models/rubric-item';

@Component({
  selector: 'app-agent-demo',
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-demo.html',
  styleUrl: './agent-demo.css',
})
export class AgentDemo implements OnInit {
  tools: ToolSchema[] = [];
  maxIterations = 10;

  // Returned from backend
  result: any = null;
  multiAgentResults: any[] = [];

  // Parsed final grade
  parsedOutput: any = null;

  // UI state
  isLoading = false;
  error = '';
  healthStatus = '';
  showBreakdown = true;
  showSteps = false;
  showTools = false;
  viewRaw = false;

  expandedItems = new Set<string>();

  // Upload & rubric logic
  rubricFile: File | null = null;
  rubricUploadResponse: any = null;
  rubricSchema: any = null;
  rubricSelections: { [key: string]: boolean } = {};
  expandedRubric: { [key: string]: boolean } = {};
  rubricPoints: { [key: string]: number } = {};

  // Repo upload
  submissionRepoUrl = '';
  submissionUploadResponse: any = null;

  taskSubscription: any = null;


  constructor(private agentService: Agent) {}

  ngOnInit() {
    this.loadTools();
    this.checkHealth();
  }

  loadTools() {
    this.agentService.getTools().subscribe({
      next: (tools) => (this.tools = tools),
      error: (err) => (this.error = 'Failed to load tools: ' + err.message),
    });
  }

  anySelected(): boolean {
    return Object.values(this.rubricSelections).some((v) => v === true);
  }

  // ---------------------------
  // RUBRIC UPLOAD
  // ---------------------------
  onRubricSelected(event: any) {
    const file = event.target.files?.[0];
    if (!file) return;

    this.agentService.uploadFile(file).subscribe({
      next: (res) => {
        console.log('Rubric uploaded:', res);

        this.rubricUploadResponse = res;
        this.rubricSchema = res;

        this.rubricSelections = {};
        this.expandedRubric = {};
        this.rubricPoints = {};

        res.rubric_items.forEach((item: RubricItem) => {
          this.rubricSelections[item.id] = false;
          this.expandedRubric[item.id] = false;
          this.rubricPoints[item.id] = item.max_points ?? 1;
        });
      },
      error: () => {
        this.error = 'Rubric upload failed.';
      },
    });
  }

  // ---------------------------
  // REPO UPLOAD
  // ---------------------------
  submitGithubUrl() {
    if (!this.submissionRepoUrl.trim()) {
      this.error = 'Please enter a valid repository URL.';
      return;
    }

    this.agentService.uploadGithubRepo(this.submissionRepoUrl).subscribe({
      next: (res) => {
        console.log('cloned repo:', res);
        this.submissionUploadResponse = res;
      },
      error: () => {
        this.error = 'Failed to clone repository.';
      },
    });
  }

  // ---------------------------
  // HEALTH CHECK
  // ---------------------------
  checkHealth() {
    this.agentService.healthCheck().subscribe({
      next: (health) => (this.healthStatus = health.status),
      error: () => (this.healthStatus = 'unhealthy'),
    });
  }

  // ---------------------------
  // MAIN RUN FUNCTION
  // ---------------------------
  runTask() {
    this.isLoading = true;
    this.error = '';
    this.result = null;
    this.parsedOutput = null;
    this.multiAgentResults = [];
  
    if (!this.rubricSchema) {
      this.error = 'Please upload a rubric first.';
      this.isLoading = false;
      return;
    }
  
    const selectedItems = this.rubricSchema.rubric_items.filter(
      (item: any) => this.rubricSelections[item.id]
    );
  
    if (selectedItems.length === 0) {
      this.error = 'Please select at least one rubric item.';
      this.isLoading = false;
      return;
    }
  
    const rubricMapping: any = {};
    selectedItems.forEach((item: RubricItem) => {
      rubricMapping[item.id] = {
        points: this.rubricPoints[item.id] ?? item.max_points ?? 1,
        description: item.description,
        items: item.items ?? [],
      };
    });
  
    const agentTask: AgentTask = {
      task: 'Multi-agent rubric grading',
      context: {
        rubric_items: selectedItems.map((i: any) => i.id),
        rubric: rubricMapping,
        repo_path: this.submissionUploadResponse.project_path,
      },
      max_iterations: this.maxIterations,
    };
  
    // SAVE subscription so we can cancel later
    this.taskSubscription = this.agentService.runAgent(agentTask).subscribe({
      next: (response: any) => {
        console.log('Multi-agent response:', response);
  
        // Parse multi-agent item results
        this.multiAgentResults = (response.multi_agent_results || []).map(
          (item: any) => {
            let parsed = {};
            try {
              parsed = JSON.parse(item.result?.output || '{}');
            } catch {}
            return { ...item, parsed };
          }
        );
  
        this.parsedOutput = this.computeAggregateGrade(this.multiAgentResults);
        this.result = response;
        this.isLoading = false;
        this.taskSubscription = null;
      },
      error: (err) => {
        if (err?.name === 'CanceledError') {
          console.log('Task was cancelled.');
        } else {
          this.error = 'Failed to run agent: ' + err.message;
        }
        this.isLoading = false;
        this.taskSubscription = null;
      }
    });
  }
  
  
  // ---------------------------
  // STOP TASK
  // ---------------------------
  stopTask() {
    if (this.taskSubscription) {
      this.taskSubscription.unsubscribe();
      this.taskSubscription = null;
    }
  
    // Reset UI to pre-run state
    this.isLoading = false;
    this.result = null;
    this.multiAgentResults = [];
    this.parsedOutput = null;
    this.error = '';
  
    console.log('Task stopped and reset.');
  }

  // ---------------------------
  // AGGREGATE SCORE LOGIC
  // ---------------------------
  computeAggregateGrade(results: any[]) {
    let total = 0;
    let max = 0;
    const breakdown: any = {};

    for (const r of results) {
      const parsed = r.parsed ?? {};

      total += parsed.total_score ?? 0;
      max += parsed.max_score ?? 0;

      breakdown[r.rubric_item] = {
        earned: parsed.total_score ?? 0,
        possible: parsed.max_score ?? 0,
        feedback:
          parsed.breakdown?.[r.rubric_item]?.feedback ??
          parsed.feedback ??
          ['No feedback returned.'],
      };
    }

    return {
      total_score: total,
      max_score: max,
      percentage: max > 0 ? (total / max) * 100 : 0,
      summary: `Assignment: ${total} / ${max} pts`,
      breakdown,
    };
  }

  // ---------------------------
  // UI HELPERS
  // ---------------------------
  toggleExpanded(id: string) {
    this.expandedItems.has(id)
      ? this.expandedItems.delete(id)
      : this.expandedItems.add(id);
  }

  isExpanded(id: string) {
    return this.expandedItems.has(id);
  }

  getBreakdownEntries(parsed: any) {
    if (!parsed?.breakdown) return [];
    return Object.keys(parsed.breakdown).map((key) => ({
      key,
      data: parsed.breakdown[key],
    }));
  }

  isArray(v: any) {
    return Array.isArray(v);
  }

  shortText(s: string, len = 200) {
    if (!s) return '';
    return s.length > len ? s.slice(0, len) + '…' : s;
  }

  prettyObservation(v: any): string {
    try {
      if (typeof v === 'object') return JSON.stringify(v, null, 2);
      return JSON.stringify(JSON.parse(v), null, 2);
    } catch {
      return String(v);
    }
  }

  scoreColorClass(pct: number | null) {
    if (pct == null) return 'score-neutral';
    if (pct >= 90) return 'score-high';
    if (pct >= 70) return 'score-mid';
    return 'score-low';
  }

  getPercentage() {
    const pct = this.parsedOutput?.percentage;
    return pct != null ? Math.round(pct) : null;
  }

  async copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {}
  }
}