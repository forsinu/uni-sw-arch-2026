export interface LoginRequest {
  usernameOrEmail: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email?: string | null;
  password: string;
}

export interface ChangePasswordRequest {
  oldPasswd: string;
  newPasswd: string;
}

export interface AdminCreateAccountRequest {
  username: string;
  email?: string | null;
  fedId?: string | null;
}

export interface AdminCreateAccountResponse {
  msg: string;
  userId: string;
  temporaryPassword: string;
}

export interface AccessTokenResponse {
  accessToken: string;
  tt: 'bearer';
}

export type UserAccountRole = 'DEFAULT' | 'ADMIN';
export type UserAccountStatus = 'ACTIVE' | 'SUSPENDED' | 'BANNED' | 'ARCHIVED';

export interface UserAccount {
  id: string;
  username: string;
  email?: string | null;
  userRole: UserAccountRole;
  federationId?: string | null;
  accountStatus: UserAccountStatus;
  createdAt: string;
  updatedAt?: string | null;
}

export interface UpdateAccountStatusRequest {
  status: UserAccountStatus;
  reason?: string | null;
}
