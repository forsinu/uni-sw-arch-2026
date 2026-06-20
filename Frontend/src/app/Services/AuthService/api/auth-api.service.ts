import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { AUTH_API_BASE_URL } from '../../shared/api-config';
import { MessageResponse, PaginatedResponse } from '../../shared/api.types';
import {
  AccessTokenResponse,
  AdminCreateAccountRequest,
  AdminCreateAccountResponse,
  LoginRequest,
  RegisterRequest,
  UpdateAccountStatusRequest,
  UserAccount
} from './auth-api.models';

@Injectable({
  providedIn: 'root'
})
export class AuthApiService {
  private readonly http = inject(HttpClient);
  private readonly authUrl = `${AUTH_API_BASE_URL}/auth`;
  private readonly usersUrl = `${AUTH_API_BASE_URL}/users`;
  private readonly adminUrl = `${AUTH_API_BASE_URL}/admin`;

  login(credentials: LoginRequest): Observable<AccessTokenResponse> {
    return this.http.post<AccessTokenResponse>(
      `${this.authUrl}/login`,
      credentials,
      { withCredentials: true }
    );
  }

  register(credentials: RegisterRequest): Observable<MessageResponse> {
    return this.http.post<MessageResponse>(
      `${this.authUrl}/register`,
      credentials,
      { withCredentials: true }
    );
  }

  refresh(): Observable<AccessTokenResponse> {
    return this.http.post<AccessTokenResponse>(
      `${this.authUrl}/refresh`,
      {},
      { withCredentials: true }
    );
  }

  logout(): Observable<MessageResponse> {
    return this.http.post<MessageResponse>(
      `${this.authUrl}/logout`,
      {},
      { withCredentials: true }
    );
  }

  getCurrentUser(): Observable<UserAccount> {
    return this.http.get<UserAccount>(`${this.usersUrl}/me`);
  }

  listAccounts(): Observable<PaginatedResponse<UserAccount>> {
    return this.http.get<PaginatedResponse<UserAccount>>(`${this.adminUrl}/users`, {
      params: {
        limit: 100,
        offset: 0
      }
    });
  }

  createAccount(
    payload: AdminCreateAccountRequest
  ): Observable<AdminCreateAccountResponse> {
    return this.http.post<AdminCreateAccountResponse>(
      `${this.adminUrl}/users`,
      payload
    );
  }

  updateAccountStatus(
    userId: string,
    payload: UpdateAccountStatusRequest
  ): Observable<MessageResponse> {
    return this.http.patch<MessageResponse>(
      `${this.adminUrl}/users/${userId}/status`,
      payload
    );
  }

  revokeAllAccountSessions(userId: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(
      `${this.adminUrl}/users/${userId}/sessions`
    );
  }
}
