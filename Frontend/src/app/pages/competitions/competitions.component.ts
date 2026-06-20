import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { catchError, debounceTime, distinctUntilChanged, of, startWith, switchMap, tap } from 'rxjs';

import { CompetitionApiService } from '../../Services/CompetitionService/api/competition-api.service';
import { SwimMeeting } from '../../Services/CompetitionService/api/competition-api.models';

@Component({
  selector: 'app-competitions',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './competitions.component.html',
  styleUrls: ['./competitions.component.scss']
})
export class CompetitionsComponent {
  private readonly competitionApi = inject(CompetitionApiService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly searchControl = new FormControl('', { nonNullable: true });
  protected readonly competitions = signal<SwimMeeting[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);

  constructor() {
    this.searchControl.valueChanges
      .pipe(
        startWith(this.searchControl.value),
        debounceTime(250),
        distinctUntilChanged(),
        tap(() => {
          this.loading.set(true);
          this.error.set(null);
        }),
        switchMap((search) =>
          this.competitionApi.listCompetitions(search).pipe(
            catchError(() => {
              this.error.set('Unable to load competitions for this account.');
              return of([]);
            })
          )
        ),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe((competitions) => {
        this.competitions.set(competitions);
        this.loading.set(false);
      });
  }
}