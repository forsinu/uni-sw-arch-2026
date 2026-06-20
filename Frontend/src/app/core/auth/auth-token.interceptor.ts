import { inject } from '@angular/core';
import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { ACCESS_TOKEN_STORAGE_KEY, API_HOST } from '../../Services/shared/api-config';
import { AuthService } from './auth.service';

const AUTH_PUBLIC_PATHS = ['/auth/api/v1/auth/login', '/auth/api/v1/auth/register'];

export const authTokenInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!request.url.startsWith(API_HOST)) {
    return next(request);
  }

  const token =
    typeof window === 'undefined'
      ? null
      : window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

  const authedRequest = token
    ? request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      })
    : request;

  return next(authedRequest).pipe(
    catchError((error: unknown) => {
      const isPublicAuthRequest = AUTH_PUBLIC_PATHS.some((path) =>
        request.url.includes(path)
      );

      if (
        error instanceof HttpErrorResponse &&
        error.status === 401 &&
        !isPublicAuthRequest
      ) {
        auth.clearSession();
        void router.navigate(['/login'], {
          queryParams: {
            returnUrl: router.url && router.url !== '/login' ? router.url : '/dashboard'
          }
        });
      }

      return throwError(() => error);
    })
  );
};