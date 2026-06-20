import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  of,
  startWith,
  switchMap,
  tap
} from 'rxjs';

import {
  FEDERATION_BACKEND_ROLE_LABEL,
  FederationMember,
  FederationMemberBackendRole
} from '../../Services/FederationService/api/federation-api.models';
import { FederationApiService } from '../../Services/FederationService/api/federation-api.service';

@Component({
  selector: 'app-athletes',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './athletes.component.html',
  styleUrls: ['./athletes.component.scss']
})
export class AthletesComponent {
  private readonly federationApi = inject(FederationApiService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly searchControl = new FormControl('', { nonNullable: true });
  protected readonly athletes = signal<FederationMember[]>([]);
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
          this.federationApi.listAthletes(search).pipe(
            catchError(() => {
              this.error.set('Unable to load athletes right now.');
              return of([]);
            })
          )
        ),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe((athletes) => {
        this.athletes.set(athletes);
        this.loading.set(false);
      });
  }

  protected roleLabel(role: FederationMemberBackendRole): string {
    return FEDERATION_BACKEND_ROLE_LABEL[role] ?? role;
  }
}
