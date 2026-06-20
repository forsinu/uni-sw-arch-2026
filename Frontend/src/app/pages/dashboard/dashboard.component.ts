import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { catchError, forkJoin, of } from 'rxjs';

import { AuthApiService } from '../../Services/AuthService/api/auth-api.service';
import { UserAccount } from '../../Services/AuthService/api/auth-api.models';
import { CompetitionApiService } from '../../Services/CompetitionService/api/competition-api.service';
import { SwimMeeting } from '../../Services/CompetitionService/api/competition-api.models';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {
  private readonly authApi = inject(AuthApiService);
  private readonly competitionApi = inject(CompetitionApiService);
  protected readonly auth = inject(AuthService);

  protected readonly loading = signal(true);
  protected readonly account = signal<UserAccount | null>(null);
  protected readonly meetings = signal<SwimMeeting[]>([]);
  protected readonly error = signal<string | null>(null);

  constructor() {
    forkJoin({
      account: this.authApi.getCurrentUser().pipe(catchError(() => of(null))),
      meetings: this.competitionApi.listMeetings().pipe(catchError(() => of([])))
    }).subscribe(({ account, meetings }) => {
      this.account.set(account);
      this.meetings.set(meetings.slice(0, 5));
      this.loading.set(false);

      if (!account) {
        this.error.set('Unable to load account details. Please sign in again.');
      }
    });
  }

  protected roleLabel(): string {
    const context = this.auth.federationContext();

    if (context.userRole === 'ADMIN') {
      return 'Administrator';
    }

    if (context.federationRole === 'COA') {
      return 'Coach';
    }

    if (context.federationRole === 'MGR') {
      return 'Team manager';
    }

    if (context.federationRole === 'REF') {
      return 'Referee';
    }

    return 'Athlete / default user';
  }
}