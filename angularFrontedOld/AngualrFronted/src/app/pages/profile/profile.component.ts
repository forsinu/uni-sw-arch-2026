import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import {
  catchError,
  finalize,
  forkJoin,
  map,
  Observable,
  of,
  switchMap,
  tap
} from 'rxjs';

import { AuthApiService } from '../../Services/AuthService/api/auth-api.service';
import {
  UserAccount,
  UserAccountStatus
} from '../../Services/AuthService/api/auth-api.models';
import {
  FEDERATION_BACKEND_ROLE_LABEL,
  FederationMember,
  FederationMemberBackendRole,
  FederationMemberRole,
  SwimmingPool,
  SwimmingTeam
} from '../../Services/FederationService/api/federation-api.models';
import { FederationApiService } from '../../Services/FederationService/api/federation-api.service';
import {
  RaceResultSummary,
  SwimEvent,
  SwimMeeting
} from '../../Services/CompetitionService/api/competition-api.models';
import { CompetitionApiService } from '../../Services/CompetitionService/api/competition-api.service';
import { AuthService } from '../../core/auth/auth.service';

interface CoachData {
  teamAthletes: FederationMember[];
  availableMeetings: SwimMeeting[];
}

type AdminSection = 'lists' | 'create';

const MEMBER_ROLE_LABELS: Record<FederationMemberRole, string> = {
  ATHLETE: 'Athlete',
  COACH: 'Coach',
  TEAM_MANAGER: 'Team manager',
  REFEREE: 'Referee'
};

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent {
  private readonly authApi = inject(AuthApiService);
  private readonly auth = inject(AuthService);
  private readonly federationApi = inject(FederationApiService);
  private readonly competitionApi = inject(CompetitionApiService);
  private readonly formBuilder = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly memberRoleFilters: FederationMemberRole[] = [
    'ATHLETE',
    'COACH',
    'TEAM_MANAGER',
    'REFEREE'
  ];
  protected readonly memberCreateRoles: Array<{
    label: string;
    value: FederationMemberBackendRole;
  }> = [
    { label: 'Athlete', value: 'ATH' },
    { label: 'Coach', value: 'COA' },
    { label: 'Team manager', value: 'MGR' },
    { label: 'Referee', value: 'REF' }
  ];
  protected readonly accountStatuses: UserAccountStatus[] = [
    'ACTIVE',
    'SUSPENDED',
    'BANNED',
    'ARCHIVED'
  ];
  protected readonly poolTypes = ['INDOOR', 'OUTDOOR'] as const;
  protected readonly poolLengths = [25, 50] as const;

  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);
  protected readonly actionMessage = signal<string | null>(null);
  protected readonly actionError = signal<string | null>(null);
  protected readonly saving = signal(false);
  protected readonly adminSection = signal<AdminSection>('lists');

  protected readonly account = signal<UserAccount | null>(null);
  protected readonly federationMember = signal<FederationMember | null>(null);
  protected readonly team = signal<SwimmingTeam | null>(null);
  protected readonly recentRaces = signal<RaceResultSummary[]>([]);
  protected readonly coachTeamAthletes = signal<FederationMember[]>([]);
  protected readonly coachMeetings = signal<SwimMeeting[]>([]);
  protected readonly coachEvents = signal<SwimEvent[]>([]);
  protected readonly coachEventsLoading = signal(false);

  protected readonly adminTeams = signal<SwimmingTeam[]>([]);
  protected readonly adminPools = signal<SwimmingPool[]>([]);
  protected readonly adminMembers = signal<FederationMember[]>([]);
  protected readonly adminAccounts = signal<UserAccount[]>([]);
  protected readonly adminMeetings = signal<SwimMeeting[]>([]);
  protected readonly selectedMemberRole = signal<FederationMemberRole>('ATHLETE');
  protected readonly adminMembersLoading = signal(false);
  protected readonly adminMembersError = signal<string | null>(null);

  protected readonly adminMemberForm = this.formBuilder.nonNullable.group({
    fedRole: ['ATH', [Validators.required]],
    teamId: [''],
    firstName: ['', [Validators.required, Validators.maxLength(100)]],
    lastName: ['', [Validators.required, Validators.maxLength(100)]],
    birth: [''],
    memberCode: ['']
  });

  protected readonly adminAccountForm = this.formBuilder.nonNullable.group({
    username: [
      '',
      [Validators.required, Validators.minLength(3), Validators.maxLength(32)]
    ],
    email: ['', [Validators.email, Validators.maxLength(320)]],
    fedId: ['']
  });

  protected readonly adminTeamForm = this.formBuilder.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(128)]],
    shortName: ['']
  });

  protected readonly adminPoolForm = this.formBuilder.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    poolType: ['INDOOR', [Validators.required]],
    poolLength: [25, [Validators.required]],
    laneCount: [8, [Validators.required, Validators.min(1), Validators.max(20)]],
    streetAddress: ['', [Validators.required, Validators.minLength(2)]],
    city: ['', [Validators.required, Validators.minLength(2)]],
    postalCode: ['', [Validators.required, Validators.minLength(2)]],
    countryIso: ['IT', [Validators.required, Validators.minLength(2), Validators.maxLength(2)]],
    teamId: ['']
  });

  protected readonly managerMeetingForm = this.formBuilder.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    poolLength: [25, [Validators.required]],
    entriesOpenAt: ['', [Validators.required]],
    entriesCloseAt: ['', [Validators.required]],
    startDate: ['', [Validators.required]],
    endDate: ['', [Validators.required]],
    swimmingPoolId: ['']
  });

  protected readonly coachEntryForm = this.formBuilder.nonNullable.group({
    meetingId: ['', [Validators.required]],
    eventId: ['', [Validators.required]],
    federationId: ['', [Validators.required, Validators.minLength(4)]],
    entryTimeMs: [60000, [Validators.required, Validators.min(1)]]
  });

  constructor() {
    this.loadProfile();

    this.coachEntryForm.controls.meetingId.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((meetingId) => this.loadCoachEvents(meetingId));
  }

  protected isAdmin(): boolean {
    return this.account()?.userRole === 'ADMIN';
  }

  protected isCoach(): boolean {
    return (
      this.federationMember()?.fedRole === 'COA' ||
      this.auth.federationContext().federationRole === 'COA'
    );
  }

  protected isTeamManager(): boolean {
    return (
      this.federationMember()?.fedRole === 'MGR' ||
      this.auth.federationContext().federationRole === 'MGR'
    );
  }

  protected profileRoleLabel(): string {
    if (this.isAdmin()) {
      return 'Admin';
    }

    const memberRole =
      this.federationMember()?.fedRole ??
      this.auth.federationContext().federationRole;

    if (memberRole) {
      return FEDERATION_BACKEND_ROLE_LABEL[memberRole] ?? memberRole;
    }

    return 'Default';
  }

  protected activeTeamId(): string | null {
    return (
      this.federationMember()?.teamId ??
      this.auth.federationContext().teamId ??
      null
    );
  }

  protected backendRoleLabel(role: FederationMemberBackendRole): string {
    return FEDERATION_BACKEND_ROLE_LABEL[role] ?? role;
  }

  protected memberRoleFilterLabel(role: FederationMemberRole): string {
    return MEMBER_ROLE_LABELS[role];
  }

  protected selectMemberRole(role: FederationMemberRole): void {
    if (this.selectedMemberRole() === role) {
      return;
    }

    this.selectedMemberRole.set(role);
    this.loadAdminMembers();
  }

  protected selectAdminSection(section: AdminSection): void {
    this.adminSection.set(section);
    this.actionMessage.set(null);
    this.actionError.set(null);
  }

  protected createAccount(): void {
    if (this.adminAccountForm.invalid) {
      this.adminAccountForm.markAllAsTouched();
      return;
    }

    const value = this.adminAccountForm.getRawValue();

    this.runAction(
      this.authApi.createAccount({
        username: value.username.trim(),
        email: value.email.trim() || null,
        fedId: value.fedId.trim() || null
      }),
      (response) =>
        `Account created. Temporary password: ${response.temporaryPassword}`,
      () => {
        this.adminAccountForm.reset({
          username: '',
          email: '',
          fedId: ''
        });
        this.reloadAdminData();
      }
    );
  }

  protected createFederationMember(): void {
    if (this.adminMemberForm.invalid) {
      this.adminMemberForm.markAllAsTouched();
      return;
    }

    const value = this.adminMemberForm.getRawValue();

    this.runAction(
      this.federationApi.createMember({
        fedRole: value.fedRole as FederationMemberBackendRole,
        teamId: value.teamId.trim() || null,
        firstName: value.firstName.trim(),
        lastName: value.lastName.trim(),
        birth: value.birth || null,
        memberCode: value.memberCode.trim() || null
      }),
      'Federation member created.',
      () => {
        this.adminMemberForm.reset({
          fedRole: 'ATH',
          teamId: '',
          firstName: '',
          lastName: '',
          birth: '',
          memberCode: ''
        });
        this.loadAdminMembers();
      }
    );
  }

  protected createTeam(): void {
    if (this.adminTeamForm.invalid) {
      this.adminTeamForm.markAllAsTouched();
      return;
    }

    const value = this.adminTeamForm.getRawValue();

    this.runAction(
      this.federationApi.createTeam({
        name: value.name.trim(),
        shortName: value.shortName.trim() || null
      }),
      'Team created.',
      () => {
        this.adminTeamForm.reset({ name: '', shortName: '' });
        this.reloadAdminData();
      }
    );
  }

  protected createPool(): void {
    if (this.adminPoolForm.invalid) {
      this.adminPoolForm.markAllAsTouched();
      return;
    }

    const value = this.adminPoolForm.getRawValue();

    this.runAction(
      this.federationApi.createSwimmingPool({
        name: value.name.trim(),
        poolType: value.poolType as 'INDOOR' | 'OUTDOOR',
        poolLength: Number(value.poolLength) as 25 | 50,
        laneCount: Number(value.laneCount),
        streetAddress: value.streetAddress.trim(),
        city: value.city.trim(),
        postalCode: value.postalCode.trim(),
        countryIso: value.countryIso.trim().toUpperCase(),
        teamId: value.teamId.trim() || null
      }),
      'Swimming pool created.',
      () => {
        this.adminPoolForm.reset({
          name: '',
          poolType: 'INDOOR',
          poolLength: 25,
          laneCount: 8,
          streetAddress: '',
          city: '',
          postalCode: '',
          countryIso: 'IT',
          teamId: ''
        });
        this.reloadAdminData();
      }
    );
  }

  protected createManagerMeeting(): void {
    if (this.managerMeetingForm.invalid) {
      this.managerMeetingForm.markAllAsTouched();
      return;
    }

    const value = this.managerMeetingForm.getRawValue();

    this.runAction(
      this.competitionApi.createMeeting({
        name: value.name.trim(),
        poolLength: Number(value.poolLength) as 25 | 50,
        entriesOpenAt: new Date(value.entriesOpenAt).toISOString(),
        entriesCloseAt: new Date(value.entriesCloseAt).toISOString(),
        startDate: value.startDate,
        endDate: value.endDate,
        organizerTeamId: this.activeTeamId(),
        swimmingPoolId: value.swimmingPoolId.trim() || null,
        status: 'UPCOMING'
      }),
      'Meeting created.',
      () => {
        this.managerMeetingForm.reset({
          name: '',
          poolLength: 25,
          entriesOpenAt: '',
          entriesCloseAt: '',
          startDate: '',
          endDate: '',
          swimmingPoolId: ''
        });
      }
    );
  }

  protected subscribeAthleteToEvent(): void {
    if (this.coachEntryForm.invalid) {
      this.coachEntryForm.markAllAsTouched();
      return;
    }

    const value = this.coachEntryForm.getRawValue();

    this.runAction(
      this.competitionApi.createEventEntry(value.eventId, {
        federationId: value.federationId.trim(),
        entryTimeMs: Number(value.entryTimeMs)
      }),
      'Athlete subscribed to event.',
      () => {
        this.coachEntryForm.patchValue({
          eventId: '',
          federationId: '',
          entryTimeMs: 60000
        });
      }
    );
  }

  protected updateAccountStatus(
    account: UserAccount,
    status: UserAccountStatus
  ): void {
    this.runAction(
      this.authApi.updateAccountStatus(account.id, {
        status,
        reason: 'Updated from the Angular admin dashboard.'
      }),
      `Account ${account.username} updated to ${status}.`,
      () => this.reloadAdminData()
    );
  }

  protected revokeAccountSessions(account: UserAccount): void {
    this.runAction(
      this.authApi.revokeAllAccountSessions(account.id),
      `Sessions revoked for ${account.username}.`
    );
  }

  protected deactivateMember(member: FederationMember): void {
    this.runAction(
      this.federationApi.deactivateMember(member.id),
      `Federation member ${member.firstName} ${member.lastName} deactivated.`,
      () => this.loadAdminMembers()
    );
  }

  protected deactivateTeam(team: SwimmingTeam): void {
    this.runAction(
      this.federationApi.deactivateTeam(team.id),
      `Team ${team.name} deactivated.`,
      () => this.reloadAdminData()
    );
  }

  protected deactivatePool(pool: SwimmingPool): void {
    this.runAction(
      this.federationApi.deactivateSwimmingPool(pool.id),
      `Pool ${pool.name} deactivated.`,
      () => this.reloadAdminData()
    );
  }

  protected deleteMeeting(meeting: SwimMeeting): void {
    this.runAction(
      this.competitionApi.deleteMeeting(meeting.id),
      `Meeting ${meeting.name} deleted.`,
      () => this.reloadAdminData()
    );
  }

  private loadProfile(): void {
    this.loading.set(true);
    this.error.set(null);

    this.authApi
      .getCurrentUser()
      .pipe(
        tap((account) => this.account.set(account)),
        switchMap((account) =>
          account.userRole === 'ADMIN'
            ? this.loadAdminData()
            : this.loadPersonalData(account)
        ),
        finalize(() => this.loading.set(false)),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe({
        error: (error: unknown) => {
          this.error.set(
            this.auth.getErrorMessage(
              error,
              'Unable to load your profile information.'
            )
          );
        }
      });
  }

  private loadPersonalData(account: UserAccount): Observable<unknown> {
    return forkJoin({
      member: this.federationApi
        .getMyFederationMemberInfo(account.federationId)
        .pipe(catchError(() => of(null))),
      races: this.competitionApi
        .listRecentRacesForCurrentUser()
        .pipe(catchError(() => of([])))
    }).pipe(
      tap(({ member, races }) => {
        this.federationMember.set(member);
        this.recentRaces.set(races);
      }),
      switchMap(({ member }) => {
        const teamId = member?.teamId ?? this.auth.federationContext().teamId;
        const fedRole =
          member?.fedRole ?? this.auth.federationContext().federationRole;
        const team$ = this.federationApi
          .getTeam(teamId)
          .pipe(catchError(() => of(null)));

        const coachData$ =
          fedRole === 'COA'
            ? this.loadCoachData(teamId)
            : of({
                teamAthletes: [],
                availableMeetings: []
              });

        return forkJoin({
          team: team$,
          coachData: coachData$
        });
      }),
      tap(({ team, coachData }) => {
        this.team.set(team);
        this.coachTeamAthletes.set(coachData.teamAthletes);
        this.coachMeetings.set(coachData.availableMeetings);
      })
    );
  }

  private loadCoachData(teamId?: string | null): Observable<CoachData> {
    return forkJoin({
      teamAthletes: this.federationApi
        .getTeamAthletes(teamId)
        .pipe(catchError(() => of([]))),
      availableMeetings: this.competitionApi
        .listMeetingsAvailableForTeam(teamId)
        .pipe(catchError(() => of([])))
    });
  }

  private loadAdminData(): Observable<unknown> {
    return forkJoin({
      teams: this.federationApi.listTeams().pipe(catchError(() => of([]))),
      pools: this.federationApi.listSwimmingPools().pipe(catchError(() => of([]))),
      members: this.federationApi
        .listMembers({ role: this.selectedMemberRole() })
        .pipe(catchError(() => of([]))),
      accounts: this.authApi.listAccounts().pipe(
        map((response) => response.results),
        catchError(() => of([]))
      ),
      meetings: this.competitionApi.listMeetings().pipe(catchError(() => of([])))
    }).pipe(
      tap(({ teams, pools, members, accounts, meetings }) => {
        this.adminTeams.set(teams);
        this.adminPools.set(pools);
        this.adminMembers.set(members);
        this.adminAccounts.set(accounts);
        this.adminMeetings.set(meetings);
      })
    );
  }

  private reloadAdminData(): void {
    this.loadAdminData()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe();
  }

  private loadAdminMembers(): void {
    this.adminMembersLoading.set(true);
    this.adminMembersError.set(null);

    this.federationApi
      .listMembers({ role: this.selectedMemberRole() })
      .pipe(
        catchError(() => {
          this.adminMembersError.set('Unable to load federation members.');
          return of([]);
        }),
        finalize(() => this.adminMembersLoading.set(false)),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe((members) => this.adminMembers.set(members));
  }

  private loadCoachEvents(meetingId: string): void {
    this.coachEvents.set([]);
    this.coachEntryForm.patchValue({ eventId: '' }, { emitEvent: false });

    if (!meetingId) {
      return;
    }

    this.coachEventsLoading.set(true);

    this.competitionApi
      .listEventsByMeeting(meetingId)
      .pipe(
        catchError(() => {
          this.actionError.set('Unable to load events for this meeting.');
          return of([]);
        }),
        finalize(() => this.coachEventsLoading.set(false)),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe((events) => this.coachEvents.set(events));
  }

  private runAction<T>(
    action$: Observable<T>,
    successMessage: string | ((value: T) => string),
    afterSuccess?: () => void
  ): void {
    this.saving.set(true);
    this.actionMessage.set(null);
    this.actionError.set(null);

    action$
      .pipe(
        finalize(() => this.saving.set(false)),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe({
        next: (value) => {
          this.actionMessage.set(
            typeof successMessage === 'function'
              ? successMessage(value)
              : successMessage
          );
          afterSuccess?.();
        },
        error: (error: unknown) => {
          this.actionError.set(
            this.auth.getErrorMessage(error, 'The requested action failed.')
          );
        }
      });
  }
}
