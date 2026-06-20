import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable, of } from 'rxjs';

import { FEDERATION_API_BASE_URL } from '../../shared/api-config';
import { MessageResponse, PaginatedResponse } from '../../shared/api.types';
import {
  CreateFederationMemberRequest,
  CreateSwimmingPoolRequest,
  CreateSwimmingTeamRequest,
  FEDERATION_ROLE_TO_BACKEND,
  FederationMember,
  MemberFilters,
  SwimmingPool,
  SwimmingTeam
} from './federation-api.models';

@Injectable({
  providedIn: 'root'
})
export class FederationApiService {
  private readonly http = inject(HttpClient);

  listAthletes(search = ''): Observable<FederationMember[]> {
    return this.listMembers({ role: 'ATHLETE', search });
  }

  listMembers(filters: MemberFilters = {}): Observable<FederationMember[]> {
    const params: Record<string, string | number | boolean> = {
      includeInactive: false,
      limit: 100,
      offset: 0
    };

    if (filters.role) {
      params['fedRole'] = FEDERATION_ROLE_TO_BACKEND[filters.role];
    }

    if (filters.teamId) {
      params['teamId'] = filters.teamId;
    }

    return this.http
      .get<PaginatedResponse<FederationMember>>(
        `${FEDERATION_API_BASE_URL}/members`,
        { params }
      )
      .pipe(
        map((response) =>
          this.filterMembers(response.results, filters.search ?? '')
        )
      );
  }

  createMember(payload: CreateFederationMemberRequest): Observable<FederationMember> {
    return this.http.post<FederationMember>(
      `${FEDERATION_API_BASE_URL}/members`,
      payload
    );
  }

  deactivateMember(memberId: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(
      `${FEDERATION_API_BASE_URL}/members/${memberId}`
    );
  }

  listTeams(search = ''): Observable<SwimmingTeam[]> {
    return this.http
      .get<PaginatedResponse<SwimmingTeam>>(`${FEDERATION_API_BASE_URL}/teams`, {
        params: {
          includeInactive: false,
          limit: 100,
          offset: 0
        }
      })
      .pipe(
        map((response) => this.filterTeams(response.results, search))
      );
  }

  createTeam(payload: CreateSwimmingTeamRequest): Observable<SwimmingTeam> {
    return this.http.post<SwimmingTeam>(
      `${FEDERATION_API_BASE_URL}/teams`,
      payload
    );
  }

  deactivateTeam(teamId: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(
      `${FEDERATION_API_BASE_URL}/teams/${teamId}`
    );
  }

  listSwimmingPools(search = ''): Observable<SwimmingPool[]> {
    return this.http
      .get<PaginatedResponse<SwimmingPool>>(`${FEDERATION_API_BASE_URL}/pools`, {
        params: {
          includeInactive: false,
          limit: 100,
          offset: 0
        }
      })
      .pipe(
        map((response) => this.filterPools(response.results, search))
      );
  }

  createSwimmingPool(payload: CreateSwimmingPoolRequest): Observable<SwimmingPool> {
    return this.http.post<SwimmingPool>(
      `${FEDERATION_API_BASE_URL}/pools`,
      payload
    );
  }

  deactivateSwimmingPool(poolId: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(
      `${FEDERATION_API_BASE_URL}/pools/${poolId}`
    );
  }

  getMyFederationMemberInfo(
    federationId?: string | null
  ): Observable<FederationMember | null> {
    if (!federationId) {
      return of(null);
    }

    // TODO: Replace with a backend /members/me or lookup-by-federation-id endpoint.
    return of(null);
  }

  getTeam(teamId?: string | null): Observable<SwimmingTeam | null> {
    if (!teamId) {
      return of(null);
    }

    // TODO: Replace with a non-admin team detail endpoint if regular members need it.
    return of(null);
  }

  getTeamAthletes(teamId?: string | null): Observable<FederationMember[]> {
    if (!teamId) {
      return of([]);
    }

    // TODO: Use a dedicated coach/team endpoint if the backend exposes one.
    return this.listMembers({ role: 'ATHLETE', teamId });
  }

  private filterMembers(
    members: FederationMember[],
    search: string
  ): FederationMember[] {
    const term = search.trim().toLowerCase();

    if (!term) {
      return members;
    }

    return members.filter((member) =>
      [
        member.firstName,
        member.lastName,
        member.memberCode,
        member.federationId,
        member.fedRole
      ]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(term))
    );
  }

  private filterTeams(teams: SwimmingTeam[], search: string): SwimmingTeam[] {
    const term = search.trim().toLowerCase();

    if (!term) {
      return teams;
    }

    return teams.filter((team) =>
      [team.name, team.shortName]
        .filter(Boolean)
        .some((value) => value!.toLowerCase().includes(term))
    );
  }

  private filterPools(pools: SwimmingPool[], search: string): SwimmingPool[] {
    const term = search.trim().toLowerCase();

    if (!term) {
      return pools;
    }

    return pools.filter((pool) =>
      [pool.name, pool.city, pool.countryIso, pool.poolLength, pool.poolType]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(term))
    );
  }
}
