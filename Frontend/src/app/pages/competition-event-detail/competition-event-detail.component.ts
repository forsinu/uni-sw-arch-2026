import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { catchError, forkJoin, Observable, of } from 'rxjs';

import { CompetitionApiService } from '../../Services/CompetitionService/api/competition-api.service';
import { RaceResultStatus, SwimEvent, SwimEventEntry, SwimEventResult } from '../../Services/CompetitionService/api/competition-api.models';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-competition-event-detail',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './competition-event-detail.component.html',
  styleUrls: ['./competition-event-detail.component.scss']
})
export class CompetitionEventDetailComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly competitionApi = inject(CompetitionApiService);
  private readonly formBuilder = inject(FormBuilder);
  private readonly auth = inject(AuthService);

  protected readonly eventId = this.route.snapshot.paramMap.get('eventId') ?? '';
  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly event = signal<SwimEvent | null>(null);
  protected readonly entries = signal<SwimEventEntry[]>([]);
  protected readonly results = signal<SwimEventResult[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly actionMessage = signal<string | null>(null);
  protected readonly actionError = signal<string | null>(null);
  protected readonly resultStatuses: RaceResultStatus[] = ['COMPLETED', 'DNS', 'DNF', 'DSQ'];

  protected readonly entryForm = this.formBuilder.nonNullable.group({
    federationId: ['', [Validators.required]],
    entryTimeMs: [60000, [Validators.required, Validators.min(1)]]
  });

  protected readonly resultForm = this.formBuilder.nonNullable.group({
    federationId: ['', [Validators.required]],
    status: ['COMPLETED' as RaceResultStatus, [Validators.required]],
    finalTimeMs: [60000, [Validators.required, Validators.min(1)]],
    disqualificationReason: ['']
  });

  constructor() {
    this.reload();
  }

  protected addEntry(): void {
    if (this.entryForm.invalid) {
      this.entryForm.markAllAsTouched();
      return;
    }

    const value = this.entryForm.getRawValue();
    this.runAction(
      () => this.competitionApi.createEventEntry(this.eventId, {
        federationId: value.federationId.trim(),
        entryTimeMs: Number(value.entryTimeMs)
      }),
      'Entry created.',
      () => this.entryForm.reset({ federationId: '', entryTimeMs: 60000 })
    );
  }

  protected saveResult(): void {
    if (this.resultForm.invalid) {
      this.resultForm.markAllAsTouched();
      return;
    }

    const value = this.resultForm.getRawValue();
    this.runAction(
      () => this.competitionApi.saveEventResults(this.eventId, [{
        federationId: value.federationId.trim(),
        status: value.status,
        finalTimeMs: value.status === 'COMPLETED' ? Number(value.finalTimeMs) : null,
        splitTimesMs: null,
        disqualificationReason: value.disqualificationReason.trim() || null
      }]),
      'Result saved.',
      () => this.resultForm.reset({ federationId: '', status: 'COMPLETED', finalTimeMs: 60000, disqualificationReason: '' })
    );
  }

  private runAction(action: () => Observable<unknown>, success: string, afterSuccess: () => void): void {
    this.saving.set(true);
    this.actionError.set(null);
    this.actionMessage.set(null);

    action().subscribe({
      next: () => {
        this.actionMessage.set(success);
        afterSuccess();
        this.saving.set(false);
        this.reload();
      },
      error: (error: unknown) => {
        this.actionError.set(this.auth.getErrorMessage(error, 'The requested action failed.'));
        this.saving.set(false);
      }
    });
  }

  private reload(): void {
    forkJoin({
      event: this.competitionApi.getEvent(this.eventId).pipe(catchError(() => of(null))),
      entries: this.competitionApi.listEventEntries(this.eventId).pipe(catchError(() => of([]))),
      results: this.competitionApi.listEventResults(this.eventId).pipe(catchError(() => of([])))
    }).subscribe(({ event, entries, results }) => {
      this.event.set(event);
      this.entries.set(entries);
      this.results.set(results);
      this.loading.set(false);
      if (!event) {
        this.error.set('Unable to load this event.');
      }
    });
  }
}