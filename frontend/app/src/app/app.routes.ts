import { Routes } from '@angular/router';

import { ChatPageComponent } from './chat/chat-page';
import { DashboardPageComponent } from './dashboard/dashboard-page';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'market-intelligence'
  },
  {
    path: 'market-intelligence',
    component: DashboardPageComponent
  },
  {
    path: 'chat',
    component: ChatPageComponent
  }
];
