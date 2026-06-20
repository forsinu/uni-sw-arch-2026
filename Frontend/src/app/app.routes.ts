import { Routes } from '@angular/router';

import { AdminComponent } from './pages/admin/admin.component';
import { AthletesComponent } from './pages/athletes/athletes.component';
import { CoachComponent } from './pages/coach/coach.component';
import { CompetitionDetailComponent } from './pages/competition-detail/competition-detail.component';
import { CompetitionEventDetailComponent } from './pages/competition-event-detail/competition-event-detail.component';
import { CompetitionsComponent } from './pages/competitions/competitions.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { HomeComponent } from './pages/home/home.component';
import { LoginComponent } from './pages/login/login.component';
import { ManagerComponent } from './pages/manager/manager.component';
import { PoolsComponent } from './pages/pools/pools.component';
import { ProfileComponent } from './pages/profile/profile.component';
import { RefereeComponent } from './pages/referee/referee.component';
import { RegisterComponent } from './pages/register/register.component';
import { TeamsComponent } from './pages/teams/teams.component';
import { authGuard } from './core/auth/auth.guard';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'home'
  },
  {
    path: 'home',
    component: HomeComponent
  },
  {
    path: 'login',
    component: LoginComponent
  },
  {
    path: 'register',
    component: RegisterComponent
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [authGuard]
  },
  {
    path: 'competitions',
    component: CompetitionsComponent,
    canActivate: [authGuard]
  },
  {
    path: 'competitions/:meetingId',
    component: CompetitionDetailComponent,
    canActivate: [authGuard]
  },
  {
    path: 'competitions/:meetingId/events/:eventId',
    component: CompetitionEventDetailComponent,
    canActivate: [authGuard]
  },
  {
    path: 'athletes',
    component: AthletesComponent,
    canActivate: [authGuard]
  },
  {
    path: 'teams',
    component: TeamsComponent,
    canActivate: [authGuard]
  },
  {
    path: 'pools',
    component: PoolsComponent,
    canActivate: [authGuard]
  },
  {
    path: 'admin',
    component: AdminComponent,
    canActivate: [authGuard]
  },
  {
    path: 'coach',
    component: CoachComponent,
    canActivate: [authGuard]
  },
  {
    path: 'manager',
    component: ManagerComponent,
    canActivate: [authGuard]
  },
  {
    path: 'referee',
    component: RefereeComponent,
    canActivate: [authGuard]
  },
  {
    path: 'profile',
    component: ProfileComponent,
    canActivate: [authGuard]
  },
  {
    path: '**',
    redirectTo: 'home'
  }
];