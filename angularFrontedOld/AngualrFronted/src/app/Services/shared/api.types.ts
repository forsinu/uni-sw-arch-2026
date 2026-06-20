export interface PaginationMetadata {
  totalRecords: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface PaginatedResponse<T> {
  metadata: PaginationMetadata;
  results: T[];
}

export interface MessageResponse {
  msg: string;
}

export function emptyPaginatedResponse<T>(): PaginatedResponse<T> {
  return {
    metadata: {
      totalRecords: 0,
      limit: 0,
      offset: 0,
      hasMore: false
    },
    results: []
  };
}
