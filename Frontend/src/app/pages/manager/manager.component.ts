import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { CompetitionApiService } from '../../Services/CompetitionService/api/competition-api.service';
import { SwimMeeting } from '../../Services/CompetitionService/api/competition-api.models';
import { SwimmingPool } from '../../Services/FederationService/api/federation-api.models';
import { FederationApiService } from '../../Services/FederationService/api/federation-api.service';
import { AuthService } from '../../core/auth/auth.service';

@Component({ selector: 'app-manager', standalone: true, imports: [ReactiveFormsModule], templateUrl: './manager.component.html', styleUrls: ['./manager.component.scss'] })
export class ManagerComponent {
  private readonly auth = inject(AuthService); private readonly competitionApi = inject(CompetitionApiService); private readonly federationApi = inject(FederationApiService); private readonly fb = inject(FormBuilder);
  protected readonly meetings = signal<SwimMeeting[]>([]); protected readonly pools = signal<SwimmingPool[]>([]); protected readonly loading = signal(true); protected readonly saving = signal(false); protected readonly error = signal<string | null>(null); protected readonly actionMessage = signal<string | null>(null); protected readonly actionError = signal<string | null>(null); protected readonly poolLengths = [25, 50] as const;
  protected readonly form = this.fb.nonNullable.group({ name: ['', [Validators.required]], poolLength: [25, [Validators.required]], entriesOpenAt: ['', [Validators.required]], entriesCloseAt: ['', [Validators.required]], startDate: ['', [Validators.required]], endDate: ['', [Validators.required]], swimmingPoolId: [''] });
  constructor() { this.reload(); }
  protected isManager(): boolean { return this.auth.federationContext().federationRole === 'MGR'; }
  protected createMeeting(): void { if (this.form.invalid) { this.form.markAllAsTouched(); return; } const v = this.form.getRawValue(); this.saving.set(true); this.actionError.set(null); this.competitionApi.createMeeting({ name: v.name.trim(), poolLength: Number(v.poolLength) as 25 | 50, entriesOpenAt: new Date(v.entriesOpenAt).toISOString(), entriesCloseAt: new Date(v.entriesCloseAt).toISOString(), startDate: v.startDate, endDate: v.endDate, organizerTeamId: this.auth.federationContext().teamId ?? null, swimmingPoolId: v.swimmingPoolId.trim() || null, status: 'UPCOMING' }).subscribe({ next: () => { this.actionMessage.set('Meeting created.'); this.form.reset({ name: '', poolLength: 25, entriesOpenAt: '', entriesCloseAt: '', startDate: '', endDate: '', swimmingPoolId: '' }); this.saving.set(false); this.reload(); }, error: (error) => { this.actionError.set(this.auth.getErrorMessage(error, 'Unable to create meeting.')); this.saving.set(false); } }); }
  private reload(): void { this.competitionApi.listMeetings().subscribe({ next: (meetings) => { this.meetings.set(meetings); this.loading.set(false); if (!this.isManager()) { this.error.set('This page is intended for team manager accounts.'); } }, error: (error) => { this.error.set(this.auth.getErrorMessage(error, 'Unable to load meetings.')); this.loading.set(false); } }); this.federationApi.listSwimmingPools().subscribe({ next: (pools) => this.pools.set(pools), error: () => this.pools.set([]) }); }
}