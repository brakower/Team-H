import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Agent, ToolSchema, AgentTask, AgentResult } from '../../services/agent';
import { RubricItem } from '../../models/rubric-item';
import { HttpEventType } from '@angular/common/http';

@Component({
  selector: 'app-agent-demo',
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-demo.html',
  styleUrl: './agent-demo.css',
})
export class AgentDemo implements OnInit {
  tools: ToolSchema[] = [];
  maxIterations: number = 10;
  result: AgentResult | null = null;
  parsedOutput: any = null;
  isLoading: boolean = false;
  error: string = '';
  healthStatus: string = '';
  // UI TOGGLES
  showBreakdown: boolean = true;
  // hide agent steps initially
  showSteps: boolean = false;
  // show tools list by default; used to collapse/expand available tools
  showTools: boolean = false;
  // show raw output toggle
  viewRaw: boolean = false;
  // expanded items (for truncation/collapse): store keys like 'step-1' or 'fb-category-0'
  expandedItems: Set<string> = new Set();
  
  rubricFile: File | null = null;
  submissionRepoUrl: string = "";
  
  rubricUploadResponse: any = null;
  submissionUploadResponse: any = null;
  
  rubricSchema: any = null;
  rubricSelections: { [key: string]: boolean } = {};
  expandedRubric: { [key: string]: boolean } = {};
  // user-set max points per rubric item
  rubricPoints: { [key: string]: number } = {};
  
  itemResults: any = {};
  totalScore: number | null = null;
  maxScore: number | null = null;
  percentage: number | null = null;


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

  anySelected(): boolean {
    if (!this.rubricSelections) return false;
    return Object.values(this.rubricSelections).some((v) => v === true);
  }
  onRubricSelected(event: any) {
    const file = event.target.files[0];
    this.rubricFile = file;

    if (File) {
      this.agentService.uploadFile(file).subscribe({
        next: (res) => {
          console.log("Rubric uploaded:", res);
          this.rubricUploadResponse = res;

          this.rubricSchema = res;
          this.rubricSelections = {};
          this.expandedRubric = {};
          this.rubricPoints = {};
          res.rubric_items.forEach((item: RubricItem) => {
            this.expandedRubric[item.id] = false;
            this.rubricSelections[item.id] = false;  // default
            // initialize rubricPoints from uploaded rubric's max_points (if provided)
            this.rubricPoints[item.id] = item.max_points ?? 1;
          });
        },
        error: (err) => {
          console.error("Rubric upload error:", err);
        }
      })
    }
  }

  submitGithubUrl() {
    this.submissionUploadResponse = null;

    if (!this.submissionRepoUrl.trim()) {
      console.error("No repository URL provided");
      return;
    }

    this.agentService.uploadGithubRepo(this.submissionRepoUrl).subscribe({
      next: (res) => {
        console.log("cloned repo: ", res);
        this.submissionUploadResponse = res;
      },
      error: (err) => {
        console.error("Github clone error: ", err);
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
    this.isLoading = true;
    this.error = '';
    this.result = null;

    const selectedItems: RubricItem[] = this.rubricSchema.rubric_items.filter(
      (item: RubricItem) => this.rubricSelections[item.id]
    );

    if (selectedItems.length === 0) {
      this.error = "Please select at least one rubric item.";
      return;
    }

    console.log("REPO PATH: " + JSON.stringify(this.submissionUploadResponse, null, 2));
    // Build a normalized rubric mapping using user-provided max points for selected items
    const rubricMapping: { [key: string]: any } = {};
    selectedItems.forEach((item: RubricItem) => {
      rubricMapping[item.id] = {
        points: this.rubricPoints[item.id] ?? item.max_points ?? 1,
        description: item.description ?? "",
      };
      if (item.items) rubricMapping[item.id].items = item.items;
    });

    const agentTask: AgentTask = {
      task: `Grade the student submission based on the following rubric criteria: ${
        selectedItems.map(i => i.title).join(", ")
      }.`,
      context: {
        // include both the selected ids and a full rubric mapping containing user-assigned max points
        rubric_items: selectedItems.map(item => item.id),
        selected_ids: selectedItems.map(item => item.id),
        rubric: rubricMapping,
        repo_path: this.submissionUploadResponse.project_path,
      } ,
      max_iterations: this.maxIterations
    };
    console.log(agentTask)

    this.agentService.runAgent(agentTask).subscribe({
      next: (result) => {
        this.result = result;
        // attempt to parse the backend output into structured JSON for nicer display
        try {
          // Primary: try the top-level result (some tools return the final aggregated grade here)
          this.parsedOutput = this.tryParseOutput(result.result?.output ?? result.result);

          // If that didn't yield a grading object (no breakdown/summary), try to find
          // a grading result in the agent steps (some agents return the final tool as an earlier step).
          const looksLikeGrade = (obj: any) => obj && (obj.breakdown || obj.summary || (typeof obj.total_score === 'number'));

          if (!looksLikeGrade(this.parsedOutput) && Array.isArray(result.steps)) {
            // search steps for a parsed observation that looks like a grade result
            for (let i = result.steps.length - 1; i >= 0; i--) {
              const step = result.steps[i];
              try {
                const parsedStep = this.tryParseOutput(step.observation ?? step.result ?? step);
                if (looksLikeGrade(parsedStep)) {
                  this.parsedOutput = parsedStep;
                  break;
                }
              } catch {
                // ignore and continue
              }
            }
          }

        } catch {
          this.parsedOutput = null;
        }
        this.isLoading = false;
      },
      error: (err) => {
        this.error = 'Failed to run task: ' + err.message;
        this.isLoading = false;
      }
    });
  }

  // Helper used by the template to iterate object keys
  objectKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }

  // Return breakdown entries as an array of { key, data } to simplify template rendering
  getBreakdownEntries(parsed: any): Array<{ key: string; data: any }> {
    if (!parsed || !parsed.breakdown) return [];
    try {
      return Object.keys(parsed.breakdown).map((k) => ({ key: k, data: parsed.breakdown[k] }));
    } catch {
      return [];
    }
  }

  // Toggle expanded state for UI sections
  toggleExpanded(id: string) {
    if (this.expandedItems.has(id)) this.expandedItems.delete(id);
    else this.expandedItems.add(id);
  }

  isExpanded(id: string): boolean {
    return this.expandedItems.has(id);
  }

  // Shorten long text for preview; used for observations and feedback
  shortText(s: any, len: number = 200): string {
    if (s === null || s === undefined) return '';
    const text = typeof s === 'string' ? s : JSON.stringify(s);
    if (text.length <= len) return text;
    return text.slice(0, len) + '…';
  }

  // Compute percentage from parsedOutput if available
  getPercentage(): number | null {
    const p = this.parsedOutput?.percentage;
    if (typeof p === 'number') return Math.round(p);
    const total = this.parsedOutput?.total_score;
    const max = this.parsedOutput?.max_score;
    if (typeof total === 'number' && typeof max === 'number' && max > 0) {
      return Math.round((total / max) * 100);
    }
    return null;
  }

  // CSS class for score color: success/medium/fail
  scoreColorClass(pct: number | null): string {
    if (pct === null) return 'score-neutral';
    if (pct >= 90) return 'score-high';
    if (pct >= 70) return 'score-mid';
    return 'score-low';
  }

  // Copy text to clipboard with graceful fallback
  async copyToClipboard(text: string) {
    try {
      if ((navigator as any)?.clipboard?.writeText) {
        await (navigator as any).clipboard.writeText(text);
      } else {
        // fallback using older API
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
    } catch (e) {
      console.warn('Copy failed', e);
    }
  }

  // Lightweight helper to detect arrays in the template
  isArray(v: any): boolean {
    return Array.isArray(v);
  }

  // Lightweight tolerant parser: tries JSON.parse, then extracts a {...} block and
  // Lightweight tolerant parser: tries JSON.parse, then extracts a balanced {...} or [...] block
  // and falls back to fixes (trailing commas, single quotes) for simple Python-style dicts/arrays.
  private tryParseOutput(raw: any): any {
    if (!raw) return null;
    if (typeof raw !== 'string') return raw;

    const text = raw.trim();

    // 1) Strict JSON
    try {
      return JSON.parse(text);
    } catch (e) {
      // continue
    }

    // Helper: find first balanced JSON object or array
    const extractBalanced = (t: string): string | null => {
      const startBrace = t.search(/[\[{]/);
      if (startBrace === -1) return null;
      let i = startBrace;
      let depth = 0;
      let inString = false;
      let escape = false;
      const openChar = t[startBrace];
      const closeChar = openChar === '{' ? '}' : ']';
      while (i < t.length) {
        const ch = t[i];
        if (escape) {
          escape = false;
        } else if (ch === '\\') {
          escape = true;
        } else if (ch === '"') {
          inString = !inString;
        } else if (!inString) {
          if (ch === openChar) depth += 1;
          else if (ch === closeChar) {
            depth -= 1;
            if (depth === 0) return t.slice(startBrace, i + 1);
          }
        }
        i += 1;
      }
      return null;
    };

    const candidate = extractBalanced(text) || text;

    // Try parsing candidate as-is
    try {
      return JSON.parse(candidate);
    } catch (e) {
      // try to fix common issues: trailing commas
      try {
        const fixed = candidate.replace(/,\s*(?=[}\]])/g, '');
        return JSON.parse(fixed);
      } catch (e2) {
        // last attempt: replace single quotes with double quotes for simple cases
        try {
          const replaced = candidate.replace(/'/g, '"');
          return JSON.parse(replaced);
        } catch (e3) {
          return null;
        }
      }
    }
  }

  // Lightweight check whether a value can be parsed as JSON or parsed by our tolerant parser
  isJsonLike(value: any): boolean {
    if (value === null || value === undefined) return false;
    if (typeof value !== 'string') return false;
    try {
      JSON.parse(value.trim());
      return true;
    } catch {
      return this.tryParseOutput(value) !== null;
    }
  }

  // Pretty-print a JSON-like observation if possible, otherwise return the original string
  prettyObservation(value: any): string {
    if (value === null || value === undefined) return '';
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    if (typeof value === 'string') {
      const parsed = this.tryParseOutput(value);
      if (parsed !== null) return JSON.stringify(parsed, null, 2);
      return value;
    }
    return String(value);
  }

  // Format action input parameters for display
  formatParameters(params: any): string {
    if (params === null || params === undefined) return '';
    if (typeof params === 'string') return params;
    try {
      return JSON.stringify(params, null, 2);
    } catch {
      return String(params);
    }
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

  gradeSelectedItems() {
    if (!this.rubricSchema || !this.rubricSelections) return;
  
    const selectedItems = this.rubricSchema.rubric_items
      .filter((i: RubricItem) => this.rubricSelections[i.id]);
  
    if (selectedItems.length === 0) {
      this.error = "Please select at least one rubric item.";
      return;
    }
  
    const payload = {
      rubric_items: selectedItems,
      submission_path: this.submissionUploadResponse?.project_path,
      options: {
        max_iterations: this.maxIterations,
        timeout: 5
      }
    };
  
    this.isLoading = true;
    this.error = "";
    this.itemResults = {}; // create a dict { itemId → {state, score, feedback} }
  
    this.agentService.gradeRubricItems(payload).subscribe({
      next: (event) => {
        if (event.type === HttpEventType.DownloadProgress) {
          // Optionally track streaming progress
        }
  
        if (event.type === HttpEventType.Response) {
          this.itemResults = event.body.items;
          this.totalScore = event.body.total_score;
          this.maxScore = event.body.max_score;
          this.percentage = event.body.percentage;
          this.isLoading = false;
        }
      },
      error: (err) => {
        this.error = "Grading failed: " + err.message;
        this.isLoading = false;
      }
    });
  }
  
  
}

