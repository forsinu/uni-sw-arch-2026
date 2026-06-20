import { HttpInterceptorFn } from '@angular/common/http';

import { ACCESS_TOKEN_STORAGE_KEY, API_HOST } from '../../Services/shared/api-config';

export const authTokenInterceptor: HttpInterceptorFn = (request, next) => {
  if (!request.url.startsWith(API_HOST)) {
    return next(request);
  }

  const token =
    typeof window === 'undefined'
      ? null
      : window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

  if (!token) {
    return next(request);
  }

  return next(
    request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    })
  );
};
