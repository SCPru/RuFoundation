import {wFetch} from "../util/fetch-util";

export interface VotesData {
    rating: number
}

export interface Vote {
    vote: number
}

export function fetchVotes(id: string): Promise<VotesData> {
    return wFetch<VotesData>(`/api/articles/${id}/votes`);
}

export async function updateVotes(id: string, data: Vote): Promise<VotesData> {
    return await wFetch(`/api/articles/${id}/votes`, {method: 'PUT', sendJson: true, body: data});
}