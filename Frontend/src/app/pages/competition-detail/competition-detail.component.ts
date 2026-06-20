import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, forkJoin, of } from 'rxjs';

import { CompetitionApiService } from '../../Services/CompetitionService/api/competition-api.service';
import { RaceGender, RaceStroke, SwimEvent, SwimMeeting } from '../../Services/CompetitionService/api/competition-api.models';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-competition-detail',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './competition-detail.component.html',
  styleUrls: ['./competition-detail.component.scss']
})
export class CompetitionDetailComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly competitionApi = inject(CompetitionApiService);
  private readonly formBuilder = inject(FormBuilder);
  private readonly auth = inject(AuthService);

  protected readonly meetingId = this.route.snapshot.paramMap.get('meetingId') ?? '';
  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly meeting = signal<SwimMeeting | null>(null);
  protected readonly events = signal<SwimEvent[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly actionMessage = signal<string | null>(null);
  protected readonly actionError = signal<string | null>(null);
  protected readonly distances = [50, 100, 200, 400, 800, 1500] as const;
  protected readonly strokes: RaceStroke[] = ['FREESTYLE', 'BACKSTROKE', 'BREASTSTROKE', 'BUTTERFLY', 'MEDLEY'];
  protected readonly genders: RaceGender[] = ['MALE', 'FEMALE'];

  protected readonly eventForm = this.formBuilder.nonNullable.group({
    distance: [50, [Validators.required]],
    stroke: ['FREESTYLE' as RaceStroke, [Validators.required]],
    gender: ['MALE' as RaceGender, [Validators.required]],
    startAt: ['', [Validators.required]]
  });

  constructor() {
    this.reload();
  }

  protected canManageEvents(): boolean {
    return this.auth.federationContext().userRole === 'ADMIN';
  }

  protected createEvent(): void {
    if (this.eventForm.invalid) {
      this.eventForm.markAllAsTouched();
      return;
    }

    const value = this.eventForm.getRawValue();
    this.saving.set(true);
    this.actionError.set(null);
    this.actionMessage.set(null);

    this.competitionApi.createEvent(this.meetingId, {
      distance: Number(value.distance) as 50,
      stroke: value.stroke,
      gender: value.gender,
      startAt: new Date(value.startAt).toISOString()
    }).subscribe({
      next: () => {
        this.actionMessage.set('Event created.');
        this.eventForm.reset({ distance: 50, stroke: 'FREESTYLE', gender: 'MALE', startAt: '' });
        this.saving.set(false);
        this.reload();
      },
      error: (error: unknown) => {
        this.actionError.set(this.auth.getErrorMessage(error, 'Unable to create event.'));
        this.saving.set(false);
      }
    });
  }

  private reload(): void {
    forkJoin({
      meeting: this.competitionApi.getMeeting(this.meetingId).pipe(catchError(() => of(null))),
      events: this.competitionApi.listEventsByMeeting(this.meetingId).pipe(catchError(() => of([])))
    }).subscribe(({ meeting, events }) => {
      this.meeting.set(meeting);
      this.events.set(events);
      this.loading.set(false);
      if (!meeting) {
        this.error.set('Unable to load this meeting.');
      }
    });
  }
}