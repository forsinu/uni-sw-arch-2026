import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators
} from '@angular/forms';
import { Router } from '@angular/router';
import { catchError, finalize, forkJoin, of } from 'rxjs';

import { AuthApiService } from '../../Services/AuthService/api/auth-api.service';
import { UserAccount } from '../../Services/AuthService/api/auth-api.models';
import { FederationMember, SwimmingTeam, FEDERATION_BACKEND_ROLE_LABEL } from '../../Services/FederationService/api/federation-api.models';
import { FederationApiService } from '../../Services/FederationService/api/federation-api.service';
import { AuthService } from '../../core/auth/auth.service';

const PASSWORD_MATCH_VALIDATOR = (
  control: AbstractControl
): ValidationErrors | null => {
  const newPasswd = control.get('newPasswd')?.value;
  const confirmNewPasswd = control.get('confirmNewPasswd')?.value;

  if (!newPasswd || !confirmNewPasswd) {
    return null;
  }

  return newPasswd === confirmNewPasswd ? null : { passwordMismatch: true };
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
  private readonly federationApi = inject(FederationApiService);
  private readonly formBuilder = inject(FormBuilder);
  private readonly router = inject(Router);
  protected readonly auth = inject(AuthService);

  protected readonly loading = signal(true);
  protected readonly account = signal<UserAccount | null>(null);
  protected readonly member = signal<FederationMember | null>(null);
  protected readonly team = signal<SwimmingTeam | null>(null);
  protected readonly error = signal<string | null>(null);
  protected readonly passwordLoading = signal(false);
  protected readonly passwordError = signal<string | null>(null);
  protected readonly passwordSuccess = signal<string | null>(null);

  protected readonly passwordForm = this.formBuilder.nonNullable.group(
    {
      oldPasswd: [
        '',
        [Validators.required, Validators.minLength(8), Validators.maxLength(128)]
      ],
      newPasswd: [
        '',
        [Validators.required, Validators.minLength(8), Validators.maxLength(128)]
      ],
      confirmNewPasswd: ['', [Validators.required]]
    },
    {
      validators: PASSWORD_MATCH_VALIDATOR
    }
  );

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

  protected changePassword(): void {
    this.passwordError.set(null);
    this.passwordSuccess.set(null);

    if (this.passwordForm.invalid) {
      this.passwordForm.markAllAsTouched();
      return;
    }

    const { oldPasswd, newPasswd } = this.passwordForm.getRawValue();

    this.passwordLoading.set(true);

    this.authApi
      .changeCurrentUserPassword({ oldPasswd, newPasswd })
      .pipe(finalize(() => this.passwordLoading.set(false)))
      .subscribe({
        next: (response) => {
          this.passwordForm.reset();
          this.passwordSuccess.set(
            response.msg || 'Password changed. Please sign in again.'
          );
          this.auth.clearSession();

          window.setTimeout(() => {
            void this.router.navigateByUrl('/login');
          }, 1200);
        },
        error: (error: unknown) => {
          this.passwordError.set(
            this.auth.getErrorMessage(error, 'Unable to change password.')
          );
        }
      });
  }

  protected passwordFieldInvalid(
    fieldName: 'oldPasswd' | 'newPasswd' | 'confirmNewPasswd'
  ): boolean {
    const field = this.passwordForm.controls[fieldName];
    return field.invalid && (field.dirty || field.touched);
  }

  protected passwordMismatch(): boolean {
    const confirmNewPasswd = this.passwordForm.controls.confirmNewPasswd;
    return (
      this.passwordForm.hasError('passwordMismatch') &&
      (confirmNewPasswd.dirty || confirmNewPasswd.touched)
    );
  }
}
