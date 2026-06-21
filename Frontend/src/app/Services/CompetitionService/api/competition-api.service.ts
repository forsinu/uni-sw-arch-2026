import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, Observable, of } from 'rxjs';

import { COMPETITION_API_BASE_URL } from '../../shared/api-config';
import { MessageResponse, PaginatedResponse } from '../../shared/api.types';
import {
  CreateSwimEventEntryRequest,
  CreateSwimEventRequest,
  CreateSwimMeetingRequest,
  RaceResultSummary,
  SwimEvent,
  SwimEventEntry,
  SwimEventResult,
  SwimMeeting,
  SwimMeetingReferee,
  SwimMeetingRefereeRequest,
  UpdateSwimEventEntryRequest,
  UpdateSwimEventRequest,
  UpdateSwimMeetingRequest,
  UpsertSwimEventResultRequest
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
      .get<PaginatedResponse<SwimMeeting>>(`${COMPETITION_API_BASE_URL}/meetings`, {
        params: {
          limit: 100,
          offset: 0
        }
      })
      .pipe(map((response) => this.filterMeetings(response.results, search)));
  }

  getMeeting(meetingId: string): Observable<SwimMeeting> {
    return this.http.get<SwimMeeting>(`${COMPETITION_API_BASE_URL}/meetings/${meetingId}`);
  }

  createMeeting(payload: CreateSwimMeetingRequest): Observable<SwimMeeting> {
    return this.http.post<SwimMeeting>(`${COMPETITION_API_BASE_URL}/meetings`, payload);
  }

  updateMeeting(meetingId: string, payload: UpdateSwimMeetingRequest): Observable<SwimMeeting> {
    return this.http.patch<SwimMeeting>(`${COMPETITION_API_BASE_URL}/meetings/${meetingId}`, payload);
  }

  updateMeetingStatus(meetingId: string, status: string): Observable<SwimMeeting> {
    return this.http.patch<SwimMeeting>(`${COMPETITION_API_BASE_URL}/meetings/${meetingId}/status`, { status });
  }

  deleteMeeting(meetingId: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(`${COMPETITION_API_BASE_URL}/meetings/${meetingId}`);
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

  getEvent(eventId: string): Observable<SwimEvent> {
    return this.http.get<SwimEvent>(`${COMPETITION_API_BASE_URL}/events/${eventId}`);
  }

  createEvent(meetingId: string, payload: CreateSwimEventRequest): Observable<SwimEvent> {
    return this.http.post<SwimEvent>(`${COMPETITION_API_BASE_URL}/meetings/${meetingId}/events`, payload);
  }

  updateEvent(eventId: string, payload: UpdateSwimEventRequest): Observable<SwimEvent> {
    return this.http.patch<SwimEvent>(`${COMPETITION_API_BASE_URL}/events/${eventId}`, payload);
  }

  deleteEvent(eventId: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(`${COMPETITION_API_BASE_URL}/events/${eventId}`);
  }

  listEventEntries(eventId: string): Observable<SwimEventEntry[]> {
    return this.http
      .get<PaginatedResponse<SwimEventEntry>>(
        `${COMPETITION_API_BASE_URL}/events/${eventId}/entries`,
        {
          params: {
            limit: 100,
            offset: 0
          }
        }
      )
      .pipe(map((response) => response.results));
  }

  createEventEntry(eventId: string, payload: CreateSwimEventEntryRequest): Observable<SwimEventEntry> {
    return this.http.post<SwimEventEntry>(`${COMPETITION_API_BASE_URL}/events/${eventId}/entries`, payload);
  }

  updateEventEntry(entryId: string, payload: UpdateSwimEventEntryRequest): Observable<SwimEventEntry> {
    return this.http.patch<SwimEventEntry>(`${COMPETITION_API_BASE_URL}/entries/${entryId}`, payload);
  }

  deleteEventEntry(entryId: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(`${COMPETITION_API_BASE_URL}/entries/${entryId}`);
  }

  listEventResults(eventId: string): Observable<SwimEventResult[]> {
    return this.http
      .get<PaginatedResponse<SwimEventResult>>(
        `${COMPETITION_API_BASE_URL}/events/${eventId}/results`,
        {
          params: {
            limit: 100,
            offset: 0
          }
        }
      )
      .pipe(map((response) => response.results));
  }

  saveEventResults(eventId: string, payload: UpsertSwimEventResultRequest[]): Observable<SwimEventResult[]> {
    return this.http.put<SwimEventResult[]>(`${COMPETITION_API_BASE_URL}/events/${eventId}/results`, payload);
  }

  deleteResult(resultId: string): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(`${COMPETITION_API_BASE_URL}/results/${resultId}`);
  }

  addMeetingReferee(payload: SwimMeetingRefereeRequest): Observable<SwimMeetingReferee> {
    return this.http.post<SwimMeetingReferee>(`${COMPETITION_API_BASE_URL}/referees`, payload);
  }

  removeMeetingReferee(payload: SwimMeetingRefereeRequest): Observable<MessageResponse> {
    return this.http.delete<MessageResponse>(`${COMPETITION_API_BASE_URL}/referees`, { body: payload });
  }

  listMeetingReferees(meetingId: string): Observable<SwimMeetingReferee[]> {
    return this.http
      .get<PaginatedResponse<SwimMeetingReferee>>(
        `${COMPETITION_API_BASE_URL}/referees/meetings/${meetingId}`,
        {
          params: {
            limit: 100,
            offset: 0
          }
        }
      )
      .pipe(map((response) => response.results));
  }

  listMyRefereeMeetings(): Observable<SwimMeetingReferee[]> {
    return this.http
      .get<PaginatedResponse<SwimMeetingReferee>>(
        `${COMPETITION_API_BASE_URL}/referees/me/meetings`,
        {
          params: {
            limit: 100,
            offset: 0
          }
        }
      )
      .pipe(map((response) => response.results));
  }

  listRecentRacesForCurrentUser(): Observable<RaceResultSummary[]> {
    return of([]);
  }

  listMeetingsAvailableForTeam(teamId?: string | null): Observable<SwimMeeting[]> {
    if (!teamId) {
      return of([]);
    }

    return this.listMeetings();
  }

  private filterMeetings(meetings: SwimMeeting[], search: string): SwimMeeting[] {
    const term = search.trim().toLowerCase();

    if (!term) {
      return meetings;
    }

    return meetings.filter((meeting) =>
      [meeting.name, meeting.status, meeting.poolLength, meeting.startDate, meeting.endDate]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(term))
    );
  }
}