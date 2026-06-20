import { Component, inject, signal } from '@angular/core';
import { catchError, forkJoin, of } from 'rxjs';

import { AuthApiService } from '../../Services/AuthService/api/auth-api.service';
import { UserAccount } from '../../Services/AuthService/api/auth-api.models';
import { FederationMember, SwimmingTeam, FEDERATION_BACKEND_ROLE_LABEL } from '../../Services/FederationService/api/federation-api.models';
import { FederationApiService } from '../../Services/FederationService/api/federation-api.service';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent {
  private readonly authApi = inject(AuthApiService);
  private readonly federationApi = inject(FederationApiService);
  protected readonly auth = inject(AuthService);

  protected readonly loading = signal(true);
  protected readonly account = signal<UserAccount | null>(null);
  protected readonly member = signal<FederationMember | null>(null);
  protected readonly team = signal<SwimmingTeam | null>(null);
  protected readonly error = signal<string | null>(null);

  constructor() {
    this.authApi
      .getCurrentUser()
      .pipe(catchError((error: unknown) => {
        this.error.set(this.auth.getErrorMessage(error, 'Unable to load profile.'));
        return of(null);
      }))
      .subscribe((account) => {
        this.account.set(account);

        if (!account) {
          this.loading.set(false);
          return;
        }

        const context = this.auth.federationContext();
        forkJoin({
          member: this.federationApi.getMyFederationMemberInfo(account.federationId).pipe(catchError(() => of(null))),
          team: this.federationApi.getTeam(context.teamId).pipe(catchError(() => of(null)))
        }).subscribe(({ member, team }) => {
          this.member.set(member);
          this.team.set(team);
          this.loading.set(false);
        });
      });
  }

  protected roleLabel(): string {
    const role = this.member()?.fedRole ?? this.auth.federationContext().federationRole;

    if (this.account()?.userRole === 'ADMIN') {
      return 'Administrator';
    }

    return role ? FEDERATION_BACKEND_ROLE_LABEL[role] : 'Default user';
  }
}