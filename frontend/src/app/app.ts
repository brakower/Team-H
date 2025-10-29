import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AgentDemo } from './components/agent-demo/agent-demo';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, AgentDemo],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('Team-H React Agent');
}
