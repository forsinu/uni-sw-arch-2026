import { Component } from '@angular/core';
import { inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthService } from '../../core/auth/auth.service';

const PASSWORD_MATCH_VALIDATOR = (
  control: AbstractControl
): ValidationErrors | null => {
  const password = control.get('password')?.value;
  const confirmPassword = control.get('confirmPassword')?.value;

  if (!password || !confirmPassword) {
    return null;
  }

  return password === confirmPassword ? null : { passwordMismatch: true };
};

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent {
  private readonly auth = inject(AuthService);
  private readonly formBuilder = inject(FormBuilder);

  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly success = signal<string | null>(null);

  protected readonly form = this.formBuilder.nonNullable.group(
    {
      username: [
        '',
        [
          Validators.required,
          Validators.minLength(3),
          Validators.maxLength(32),
          Validators.pattern(/^[a-zA-Z0-9_](?:[a-zA-Z0-9_.]*[a-zA-Z0-9_])?$/)
        ]
      ],
      email: ['', [Validators.email, Validators.maxLength(320)]],
      password: [
        '',
        [Validators.required, Validators.minLength(8), Validators.maxLength(128)]
      ],
      confirmPassword: ['', [Validators.required]]
    },
    {
      validators: PASSWORD_MATCH_VALIDATOR
    }
  );

  protected submit(): void {
    this.error.set(null);
    this.success.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const { username, email, password } = this.form.getRawValue();

    this.loading.set(true);

    this.auth
      .register({ username, email, password })
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response) => {
          this.form.reset();
          this.success.set(response.msg || 'Account created. You can log in now.');
        },
        error: (error: unknown) => {
          this.error.set(
            this.auth.getErrorMessage(
              error,
              'Registration failed. Check the form and try again.'
            )
          );
        }
      });
  }

  protected fieldInvalid(
    fieldName: 'username' | 'email' | 'password' | 'confirmPassword'
  ): boolean {
    const field = this.form.controls[fieldName];
    return field.invalid && (field.dirty || field.touched);
  }

  protected passwordMismatch(): boolean {
    const confirmPassword = this.form.controls.confirmPassword;
    return (
      this.form.hasError('passwordMismatch') &&
      (confirmPassword.dirty || confirmPassword.touched)
    );
  }
}
