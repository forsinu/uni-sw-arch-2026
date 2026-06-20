export interface SwimMeeting {
  id: string;
  name: string;
  poolLength: string;
  status: string;
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

export interface SwimEvent {
  id: string;
  meetingId: string;
  distance: 50 | 100 | 200 | 400 | 800 | 1500;
  stroke: 'FREESTYLE' | 'BACKSTROKE' | 'BREASTSTROKE' | 'BUTTERFLY' | 'MEDLEY';
  gender: 'MALE' | 'FEMALE';
  startAt: string;
}

export interface CreateSwimEventEntryRequest {
  federationId: string;
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

export interface RaceResultSummary {
  id: string;
  meetingName: string;
  eventName: string;
  result: string;
  completedAt?: string | null;
}
