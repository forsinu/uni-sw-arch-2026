export type FederationMemberRole = 'ATHLETE' | 'COACH' | 'TEAM_MANAGER' | 'REFEREE';
export type FederationMemberBackendRole = 'ATH' | 'COA' | 'MGR' | 'REF';

export interface FederationMember {
  id: string;
  federationId: string;
  fedRole: FederationMemberBackendRole;
  teamId?: string | null;
  memberCode: string;
  firstName: string;
  lastName: string;
  birth?: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt?: string | null;
}

export interface CreateFederationMemberRequest {
  fedRole: FederationMemberBackendRole;
  teamId?: string | null;
  firstName: string;
  lastName: string;
  birth?: string | null;
  memberCode?: string | null;
}

export interface SwimmingTeam {
  id: string;
  name: string;
  shortName?: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt?: string | null;
}

export interface CreateSwimmingTeamRequest {
  name: string;
  shortName?: string | null;
}

export interface SwimmingPool {
  id: string;
  name: string;
  poolType: string;
  poolLength: string;
  laneCount: number;
  streetAddress: string;
  city: string;
  postalCode: string;
  countryIso: string;
  isActive: boolean;
  teamId?: string | null;
  createdAt: string;
  updatedAt?: string | null;
}

export interface CreateSwimmingPoolRequest {
  name: string;
  poolType: 'INDOOR' | 'OUTDOOR';
  poolLength: 25 | 50;
  laneCount: number;
  streetAddress: string;
  city: string;
  postalCode: string;
  countryIso: string;
  teamId?: string | null;
}

export interface MemberFilters {
  role?: FederationMemberRole;
  search?: string;
  teamId?: string;
}

export const FEDERATION_ROLE_TO_BACKEND: Record<
  FederationMemberRole,
  FederationMemberBackendRole
> = {
  ATHLETE: 'ATH',
  COACH: 'COA',
  TEAM_MANAGER: 'MGR',
  REFEREE: 'REF'
};

export const FEDERATION_BACKEND_ROLE_LABEL: Record<
  FederationMemberBackendRole,
  string
> = {
  ATH: 'Athlete',
  COA: 'Coach',
  MGR: 'Team manager',
  REF: 'Referee'
};
