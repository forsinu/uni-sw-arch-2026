import { HttpErrorResponse } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { catchError, Observable, of, tap } from 'rxjs';

import { AuthApiService } from '../../Services/AuthService/api/auth-api.service';
import { ACCESS_TOKEN_STORAGE_KEY } from '../../Services/shared/api-config';
import {
  AccessTokenResponse,
  LoginRequest,
  MessageResponse,
  RegisterRequest
} from './auth.models';

export interface DecodedFederationContext {
  userRole?: string;
  federationId?: string | null;
  federationRole?: 'ATH' | 'COA' | 'MGR' | 'REF' | null;
  teamId?: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly authApi = inject(AuthApiService);
  private readonly accessTokenStorageKey = ACCESS_TOKEN_STORAGE_KEY;

  readonly accessToken = signal<string | null>(this.readStoredToken());
  readonly isAuthenticated = computed(() => Boolean(this.accessToken()));
  readonly federationContext = computed(() =>
    this.decodeFederationContext(this.accessToken())
  );

  login(credentials: LoginRequest): Observable<AccessTokenResponse> {
    const body: LoginRequest = {
      usernameOrEmail: credentials.usernameOrEmail.trim(),
      password: credentials.password
    };

    return this.authApi
      .login(body)
      .pipe(tap((response) => this.storeAccessToken(response.accessToken)));
  }

  register(credentials: RegisterRequest): Observable<MessageResponse> {
    const email = credentials.email?.trim();
    const body: RegisterRequest = {
      username: credentials.username.trim(),
      email: email || null,
      password: credentials.password
    };

    return this.authApi.register(body);
  }

  refresh(): Observable<AccessTokenResponse> {
    return this.authApi
      .refresh()
      .pipe(tap((response) => this.storeAccessToken(response.accessToken)));
  }

  logout(): Observable<MessageResponse> {
    return this.authApi.logout().pipe(
      catchError(() => of({ msg: 'Logged out locally.' })),
      tap(() => this.storeAccessToken(null))
    );
  }

  getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof HttpErrorResponse) {
      if (typeof error.error?.detail === 'string') {
        return error.error.detail;
      }

      if (Array.isArray(error.error?.detail)) {
        return error.error.detail
          .map((item: { msg?: string }) => item.msg)
          .filter(Boolean)
          .join(' ');
      }

      if (typeof error.error?.msg === 'string') {
        return error.error.msg;
      }

      if (error.status === 0) {
        return 'Cannot reach the authentication service. Check that the backend is running and reachable.';
      }
    }

    return fallback;
  }

  private storeAccessToken(token: string | null): void {
    this.accessToken.set(token);

    if (!this.canUseLocalStorage()) {
      return;
    }

    if (token) {
      window.localStorage.setItem(this.accessTokenStorageKey, token);
    } else {
      window.localStorage.removeItem(this.accessTokenStorageKey);
    }
  }

  private readStoredToken(): string | null {
    if (!this.canUseLocalStorage()) {
      return null;
    }

    return window.localStorage.getItem(this.accessTokenStorageKey);
  }

  private canUseLocalStorage(): boolean {
    return typeof window !== 'undefined' && Boolean(window.localStorage);
  }

  private decodeFederationContext(token: string | null): DecodedFederationContext {
    if (!token) {
      return {};
    }

    try {
      const [, payloadPart] = token.split('.');
      const payload = JSON.parse(this.base64UrlDecode(payloadPart)) as {
        role?: string;
        fed?: string | null;
      };
      const federationId = payload.fed ?? null;
      const fedMatch = federationId?.match(
        /^(.+?)-([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})-.*$/
      );

      return {
        userRole: payload.role,
        federationId,
        federationRole: fedMatch?.[1] as DecodedFederationContext['federationRole'],
        teamId: fedMatch?.[2] ?? null
      };
    } catch {
      return {};
    }
  }

  private base64UrlDecode(value: string | undefined): string {
    if (!value) {
      return '{}';
    }

    const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      '='
    );

    return window.atob(padded);
  }
}
