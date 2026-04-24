import { Routes } from '@angular/router';

import { ChatPageComponent } from './chat/chat-page';
import { DashboardPageComponent } from './dashboard/dashboard-page';

export const routes: Routes = [
  {
    path: '',
    component: DashboardPageComponent
  },
  {
    path: 'chat',
    component: ChatPageComponent
  }
];
