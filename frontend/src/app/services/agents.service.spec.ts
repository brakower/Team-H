import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Agent, ToolSchema, AgentTask, ToolExecution } from '/workspaces/Team-H/frontend/src/app/services/agent';

describe('Agent Service', () => {
  let service: Agent;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [Agent]
    });

    service = TestBed.inject(Agent);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should fetch all tools', () => {
    const mockTools: ToolSchema[] = [{ name: 'calculator', description: 'Calc', parameters: {} }];

    service.getTools().subscribe(tools => {
      expect(tools.length).toBe(1);
      expect(tools[0].name).toBe('calculator');
    });

    const req = httpMock.expectOne('http://localhost:8000/tools');
    expect(req.request.method).toBe('GET');
    req.flush(mockTools);
  });

  it('should fetch tool schema', () => {
    const mockSchema: ToolSchema = { name: 'calculator', description: 'Calc', parameters: {} };
    service.getToolSchema('calculator').subscribe(schema => {
      expect(schema.name).toBe('calculator');
    });

    const req = httpMock.expectOne('http://localhost:8000/tools/calculator');
    expect(req.request.method).toBe('GET');
    req.flush(mockSchema);
  });

  it('should run agent task', () => {
    const task: AgentTask = { task: 'perform calculation' };
    const mockResult = { result: { output: 'done', steps: [] }, log: 'log', steps: [] };

    service.runAgent(task).subscribe(res => {
      expect(res.result.output).toBe('done');
      expect(res.log).toBe('log');
    });

    const req = httpMock.expectOne('http://localhost:8000/run');
    expect(req.request.method).toBe('POST');
    req.flush(mockResult);
  });

  it('should execute a tool', () => {
    const execution: ToolExecution = { tool_name: 'calculator', parameters: { a: 5, b: 3 } };
    const mockResponse = { tool: 'calculator', result: 8 };

    service.executeTool(execution).subscribe(res => {
      expect(res.tool).toBe('calculator');
      expect(res.result).toBe(8);
    });

    const req = httpMock.expectOne('http://localhost:8000/execute');
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);
  });

  it('should discover tools', () => {
    const mockDiscover = { calculator: { description: 'Calc', parameters: {} } };
    service.discoverTools().subscribe(res => {
      expect(res.calculator).toBeDefined();
    });

    const req = httpMock.expectOne('http://localhost:8000/discover');
    expect(req.request.method).toBe('GET');
    req.flush(mockDiscover);
  });

  it('should check health', () => {
    service.healthCheck().subscribe(res => {
      expect(res.status).toBe('healthy');
    });

    const req = httpMock.expectOne('http://localhost:8000/health');
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'healthy' });
  });
});
