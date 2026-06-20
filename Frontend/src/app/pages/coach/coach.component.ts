import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { catchError, forkJoin, of } from 'rxjs';
import { CompetitionApiService } from '../../Services/CompetitionService/api/competition-api.service';
import { SwimEvent, SwimMeeting } from '../../Services/CompetitionService/api/competition-api.models';
import { FederationMember } from '../../Services/FederationService/api/federation-api.models';
import { FederationApiService } from '../../Services/FederationService/api/federation-api.service';
import { AuthService } from '../../core/auth/auth.service';

@Component({ selector: 'app-coach', standalone: true, imports: [ReactiveFormsModule], templateUrl: './coach.component.html', styleUrls: ['./coach.component.scss'] })
export class CoachComponent {
  private readonly auth = inject(AuthService); private readonly federationApi = inject(FederationApiService); private readonly competitionApi = inject(CompetitionApiService); private readonly fb = inject(FormBuilder);
  protected readonly athletes = signal<FederationMember[]>([]); protected readonly meetings = signal<SwimMeeting[]>([]); protected readonly events = signal<SwimEvent[]>([]); protected readonly loading = signal(true); protected readonly saving = signal(false); protected readonly error = signal<string | null>(null); protected readonly actionMessage = signal<string | null>(null); protected readonly actionError = signal<string | null>(null);
  protected readonly form = this.fb.nonNullable.group({ meetingId: ['', [Validators.required]], eventId: ['', [Validators.required]], federationId: ['', [Validators.required]], entryTimeMs: [60000, [Validators.required, Validators.min(1)]] });
  constructor() { this.reload(); this.form.controls.meetingId.valueChanges.subscribe((meetingId) => this.loadEvents(meetingId)); }
  protected isCoach(): boolean { return this.auth.federationContext().federationRole === 'COA'; }
  protected subscribeAthlete(): void { if (this.form.invalid) { this.form.markAllAsTouched(); return; } const v = this.form.getRawValue(); this.saving.set(true); this.actionError.set(null); this.competitionApi.createEventEntry(v.eventId, { federationId: v.federationId.trim(), entryTimeMs: Number(v.entryTimeMs) }).subscribe({ next: () => { this.actionMessage.set('Athlete subscribed.'); this.form.patchValue({ eventId: '', federationId: '', entryTimeMs: 60000 }); this.saving.set(false); }, error: (error) => { this.actionError.set(this.auth.getErrorMessage(error, 'Unable to subscribe athlete.')); this.saving.set(false); } }); }
  private reload(): void { const teamId = this.auth.federationContext().teamId; forkJoin({ athletes: this.federationApi.getTeamAthletes(teamId).pipe(catchError(() => of([]))), meetings: this.competitionApi.listMeetingsAvailableForTeam(teamId).pipe(catchError(() => of([]))) }).subscribe(({ athletes, meetings }) => { this.athletes.set(athletes); this.meetings.set(meetings); this.loading.set(false); if (!this.isCoach()) { this.error.set('This page is intended for coach accounts.'); } }); }
  private loadEvents(meetingId: string): void { this.events.set([]); this.form.patchValue({ eventId: '' }, { emitEvent: false }); if (!meetingId) { return; } this.competitionApi.listEventsByMeeting(meetingId).pipe(catchError(() => of([]))).subscribe((events) => this.events.set(events)); }
}