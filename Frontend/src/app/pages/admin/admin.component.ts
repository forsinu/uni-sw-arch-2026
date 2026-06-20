import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { catchError, forkJoin, map, Observable, of } from 'rxjs';

import { AuthApiService } from '../../Services/AuthService/api/auth-api.service';
import { UserAccount, UserAccountStatus } from '../../Services/AuthService/api/auth-api.models';
import { CompetitionApiService } from '../../Services/CompetitionService/api/competition-api.service';
import { SwimMeeting } from '../../Services/CompetitionService/api/competition-api.models';
import { FederationMember, FederationMemberBackendRole, SwimmingPool, SwimmingTeam } from '../../Services/FederationService/api/federation-api.models';
import { FederationApiService } from '../../Services/FederationService/api/federation-api.service';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.scss']
})
export class AdminComponent {
  private readonly authApi = inject(AuthApiService);
  private readonly federationApi = inject(FederationApiService);
  private readonly competitionApi = inject(CompetitionApiService);
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);

  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly actionMessage = signal<string | null>(null);
  protected readonly actionError = signal<string | null>(null);
  protected readonly accounts = signal<UserAccount[]>([]);
  protected readonly members = signal<FederationMember[]>([]);
  protected readonly teams = signal<SwimmingTeam[]>([]);
  protected readonly pools = signal<SwimmingPool[]>([]);
  protected readonly meetings = signal<SwimMeeting[]>([]);
  protected readonly roles: FederationMemberBackendRole[] = ['ATH', 'COA', 'MGR', 'REF'];
  protected readonly statuses: UserAccountStatus[] = ['ACTIVE', 'SUSPENDED', 'BANNED', 'ARCHIVED'];

  protected readonly accountForm = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.email]],
    fedId: ['']
  });
  protected readonly memberForm = this.fb.nonNullable.group({
    fedRole: ['ATH', [Validators.required]],
    teamId: [''],
    firstName: ['', [Validators.required]],
    lastName: ['', [Validators.required]],
    birth: [''],
    memberCode: ['']
  });

  constructor() {
    this.reload();
  }

  protected isAdmin(): boolean {
    return this.auth.federationContext().userRole === 'ADMIN';
  }

  protected createAccount(): void {
    if (this.accountForm.invalid) {
      this.accountForm.markAllAsTouched();
      return;
    }

    const value = this.accountForm.getRawValue();
    this.runAction(
      this.authApi.createAccount({
        username: value.username.trim(),
        email: value.email.trim() || null,
        fedId: value.fedId.trim() || null
      }),
      (response) => `Account created. Temporary password: ${response.temporaryPassword}`,
      () => {
        this.accountForm.reset({ username: '', email: '', fedId: '' });
        this.reload();
      }
    );
  }

  protected createMember(): void {
    if (this.memberForm.invalid) {
      this.memberForm.markAllAsTouched();
      return;
    }

    const value = this.memberForm.getRawValue();
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
        this.memberForm.reset({ fedRole: 'ATH', teamId: '', firstName: '', lastName: '', birth: '', memberCode: '' });
        this.reload();
      }
    );
  }

  protected updateStatus(account: UserAccount, status: UserAccountStatus): void {
    this.runAction(
      this.authApi.updateAccountStatus(account.id, { status, reason: 'Updated from Angular admin dashboard.' }),
      `Account ${account.username} set to ${status}.`,
      () => this.reload()
    );
  }

  protected deactivateMember(member: FederationMember): void {
    this.runAction(
      this.federationApi.deactivateMember(member.id),
      `Member ${member.firstName} ${member.lastName} deactivated.`,
      () => this.reload()
    );
  }

  protected deleteMeeting(meeting: SwimMeeting): void {
    this.runAction(
      this.competitionApi.deleteMeeting(meeting.id),
      `Meeting ${meeting.name} deleted.`,
      () => this.reload()
    );
  }

  private reload(): void {
    forkJoin({
      accounts: this.authApi.listAccounts().pipe(map((response) => response.results), catchError(() => of([]))),
      members: this.federationApi.listMembers().pipe(catchError(() => of([]))),
      teams: this.federationApi.listTeams().pipe(catchError(() => of([]))),
      pools: this.federationApi.listSwimmingPools().pipe(catchError(() => of([]))),
      meetings: this.competitionApi.listMeetings().pipe(catchError(() => of([])))
    }).subscribe((data) => {
      this.accounts.set(data.accounts);
      this.members.set(data.members);
      this.teams.set(data.teams);
      this.pools.set(data.pools);
      this.meetings.set(data.meetings);
      this.loading.set(false);

      if (!this.isAdmin()) {
        this.error.set('This page requires an administrator account.');
      }
    });
  }

  private runAction<T>(
    action: Observable<T>,
    success: string | ((value: T) => string),
    afterSuccess?: () => void
  ): void {
    this.saving.set(true);
    this.actionError.set(null);
    this.actionMessage.set(null);

    action.subscribe({
      next: (value) => {
        this.actionMessage.set(typeof success === 'function' ? success(value) : success);
        this.saving.set(false);
        afterSuccess?.();
      },
      error: (error) => {
        this.actionError.set(this.auth.getErrorMessage(error, 'The requested admin action failed.'));
        this.saving.set(false);
      }
    });
  }
}