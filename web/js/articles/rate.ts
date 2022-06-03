import {updateVotes, VotesData} from "../api/rate";

async function onClick(id: string, vote: number): Promise<VotesData> {
    return await updateVotes(id, {"vote": vote});
}

function updateRating(element: HTMLElement, votesData: VotesData) {
    element.innerText = String(votesData.rating);
}

export function makeRateModule(node: HTMLElement) {
    if ((node as any)._rate) {
        return
    }
    (node as any)._rate = true;

    const number: HTMLElement = node.querySelector('.number');
    const rateup: HTMLElement = node.querySelector('.rateup a');
    const ratedown: HTMLElement = node.querySelector('.ratedown a');
    const cancel: HTMLElement = node.querySelector('.cancel a');

    const callback = function (votesData) {
        updateRating(number, votesData)
    };

    rateup.onclick = function() {onClick("test", 1).then(callback)};
    ratedown.onclick = function() {onClick("test", -1).then(callback)};
    cancel.onclick = function() {onClick("test", 0).then(callback)};
}