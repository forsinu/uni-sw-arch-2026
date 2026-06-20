import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CompetitionApiService } from '../../Services/CompetitionService/api/competition-api.service';
import { SwimMeetingReferee } from '../../Services/CompetitionService/api/competition-api.models';
import { AuthService } from '../../core/auth/auth.service';

@Component({ selector: 'app-referee', standalone: true, imports: [RouterLink], templateUrl: './referee.component.html', styleUrls: ['./referee.component.scss'] })
export class RefereeComponent {
  private readonly api = inject(CompetitionApiService); protected readonly auth = inject(AuthService);
  protected readonly assignments = signal<SwimMeetingReferee[]>([]); protected readonly loading = signal(true); protected readonly error = signal<string | null>(null);
  constructor() { this.api.listMyRefereeMeetings().subscribe({ next: (assignments) => { this.assignments.set(assignments); this.loading.set(false); if (this.auth.federationContext().federationRole !== 'REF') { this.error.set('This page is intended for referee accounts.'); } }, error: (error) => { this.error.set(this.auth.getErrorMessage(error, 'Unable to load referee assignments.')); this.loading.set(false); } }); }
}