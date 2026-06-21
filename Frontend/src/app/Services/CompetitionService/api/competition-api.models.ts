export type SwimMeetingStatus = 'UPCOMING' | 'OPEN' | 'CLOSED' | 'ONGOING' | 'COMPLETED' | string;
export type RaceStroke = 'FREESTYLE' | 'BACKSTROKE' | 'BREASTSTROKE' | 'BUTTERFLY' | 'MEDLEY';
export type RaceGender = 'MALE' | 'FEMALE';
export type RaceResultStatus = 'COMPLETED' | 'DNS' | 'DNF' | 'DSQ' | string;

export interface SwimMeeting {
  id: string;
  name: string;
  poolLength: string;
  status: SwimMeetingStatus;
  entriesOpenAt: string;
  entriesCloseAt: string;
  startDate: string;
  endDate: string;
  organizerTeamId?: string | null;
  swimmingPoolId?: string | null;
  createdAt: string;
  updatedAt?: string | null;
}

export interface CreateSwimMeetingRequest {
  name: string;
  poolLength: 25 | 50;
  entriesOpenAt: string;
  entriesCloseAt: string;
  startDate: string;
  endDate: string;
  organizerTeamId?: string | null;
  swimmingPoolId?: string | null;
  status?: string;
}

export interface UpdateSwimMeetingRequest extends Partial<CreateSwimMeetingRequest> {}

export interface SwimEvent {
  id: string;
  meetingId: string;
  distance: 50 | 100 | 200 | 400 | 800 | 1500;
  stroke: RaceStroke;
  gender: RaceGender;
  startAt: string;
}

export interface CreateSwimEventRequest {
  distance: 50 | 100 | 200 | 400 | 800 | 1500;
  stroke: RaceStroke;
  gender: RaceGender;
  startAt: string;
}

export interface UpdateSwimEventRequest extends Partial<CreateSwimEventRequest> {}

export interface CreateSwimEventEntryRequest {
  federationId: string;
  entryTimeMs: number;
}

export interface UpdateSwimEventEntryRequest {
  entryTimeMs: number;
}

export interface SwimEventEntry {
  id: string;
  swimEventId: string;
  federationId: string;
  entryTimeMs: number;
  enteredBy: string;
  createdAt: string;
  updatedAt?: string | null;
}

export interface SwimEventResult {
  id: string;
  swimEventId: string;
  federationId: string;
  status: RaceResultStatus;
  finalTimeMs?: number | null;
  splitTimesMs?: number[] | null;
  disqualificationReason?: string | null;
  createdAt: string;
  updatedAt?: string | null;
}

export interface UpsertSwimEventResultRequest {
  federationId: string;
  status: RaceResultStatus;
  finalTimeMs?: number | null;
  splitTimesMs?: number[] | null;
  disqualificationReason?: string | null;
}

export interface SwimMeetingReferee {
  id: string;
  meetingId: string;
  refereeFederationId: string;
  assignedBy: string;
  createdAt: string;
}

export interface SwimMeetingRefereeRequest {
  meetingId: string;
  refereeFederationId: string;
}

export interface RaceResultSummary {
  id: string;
  meetingName: string;
  eventName: string;
  result: string;
  completedAt?: string | null;
}