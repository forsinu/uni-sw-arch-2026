import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable, of } from 'rxjs';

import { COMPETITION_API_BASE_URL } from '../../shared/api-config';
import { MessageResponse, PaginatedResponse } from '../../shared/api.types';
import {
  CreateSwimEventEntryRequest,
  CreateSwimMeetingRequest,
  RaceResultSummary,
  SwimEvent,
  SwimEventEntry,
  SwimMeeting
} from './competition-api.models';

@Injectable({
  providedIn: 'root'
})
export class CompetitionApiService {
  private readonly http = inject(HttpClient);

  listCompetitions(search = ''): Observable<SwimMeeting[]> {
    return this.listMeetings(search);
  }

  listMeetings(search = ''): Observable<SwimMeeting[]> {
    return this.http
      .get<PaginatedResponse<SwimMeeting>>(
        `${COMPETITION_API_BASE_URL}/meetings`,
        {
          params: {
            limit: 100,
            offset: 0
          }
        }
      )
      .pipe(
        map((response) => this.filterMeetings(response.results, search))
      );
  }

  createMeeting(payload: CreateSwimMeetingRequest): Observable<SwimMeeting> {
    return this.http.post<SwimMeeting>(
      `${COMPETITION_API_BASE_URL}/meetings`,
      payload
    );
  }

  deleteMeeting(meetingId: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(
      `${COMPETITION_API_BASE_URL}/meetings/${meetingId}`
    );
  }

  listEventsByMeeting(meetingId: string): Observable<SwimEvent[]> {
    return this.http
      .get<PaginatedResponse<SwimEvent>>(
        `${COMPETITION_API_BASE_URL}/meetings/${meetingId}/events`,
        {
          params: {
            limit: 100,
            offset: 0
          }
        }
      )
      .pipe(map((response) => response.results));
  }

  createEventEntry(
    eventId: string,
    payload: CreateSwimEventEntryRequest
  ): Observable<SwimEventEntry> {
    return this.http.post<SwimEventEntry>(
      `${COMPETITION_API_BASE_URL}/events/${eventId}/entries`,
      payload
    );
  }

  listRecentRacesForCurrentUser(): Observable<RaceResultSummary[]> {
    // TODO: Replace with a user-specific results endpoint when available.
    return of([]);
  }

  listMeetingsAvailableForTeam(teamId?: string | null): Observable<SwimMeeting[]> {
    if (!teamId) {
      return of([]);
    }

    // TODO: Replace with a dedicated subscription-eligibility endpoint when available.
    return this.listMeetings();
  }

  private filterMeetings(
    meetings: SwimMeeting[],
    search: string
  ): SwimMeeting[] {
    const term = search.trim().toLowerCase();

    if (!term) {
      return meetings;
    }

    return meetings.filter((meeting) =>
      [
        meeting.name,
        meeting.status,
        meeting.poolLength,
        meeting.startDate,
        meeting.endDate
      ]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(term))
    );
  }
}
