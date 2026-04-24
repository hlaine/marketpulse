import { CommonModule } from '@angular/common';
import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-stat-card',
  imports: [CommonModule],
  templateUrl: './stat-card.html',
  styleUrl: './stat-card.css'
})
export class StatCardComponent {
  readonly title = input.required<string>();
  readonly subtitle = input.required<string>();
  readonly hero = input.required<string>();
  readonly delta = input.required<string>();
  readonly selected = input(false);

  readonly select = output<void>();
}
