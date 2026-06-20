import { Component } from '@angular/core';
import { inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly formBuilder = inject(FormBuilder);
  private readonly router = inject(Router);

  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly form = this.formBuilder.nonNullable.group({
    usernameOrEmail: [
      '',
      [Validators.required, Validators.minLength(3), Validators.maxLength(320)]
    ],
    password: [
      '',
      [Validators.required, Validators.minLength(8), Validators.maxLength(128)]
    ]
  });

  protected submit(): void {
    this.error.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);

    this.auth
      .login(this.form.getRawValue())
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: () => void this.router.navigateByUrl('/home'),
        error: (error: unknown) => {
          this.error.set(
            this.auth.getErrorMessage(
              error,
              'Login failed. Check your credentials and try again.'
            )
          );
        }
      });
  }

  protected fieldInvalid(fieldName: 'usernameOrEmail' | 'password'): boolean {
    const field = this.form.controls[fieldName];
    return field.invalid && (field.dirty || field.touched);
  }
}
