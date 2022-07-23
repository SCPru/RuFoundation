import {callModule} from "../api/modules";
import {showErrorModal} from "../util/wikidot-modal";
import {ModuleRateResponse} from "../api/rate";
import {sprintf} from 'sprintf-js'

async function onClick(e: MouseEvent, pageId: string, vote: number): Promise<ModuleRateResponse> {
    e.preventDefault();
    e.stopPropagation();
    try {
        return await callModule<ModuleRateResponse>({module: 'rate', method: 'rate', pageId, params: {value: vote}});
    } catch (e) {
        showErrorModal(e.error || 'Ошибка связи с сервером');
        throw e;
    }
}

function updateRating(number: HTMLElement, votes: HTMLElement, control: HTMLElement, votesData: ModuleRateResponse) {
    number.textContent = sprintf('%.1f', votesData.rating);
    votes.textContent = sprintf('%d', votesData.voteCount);
    control.style.width = `${Math.floor(votesData.rating * 20)}%`;
}

export function makeStarsRateModule(node: HTMLElement) {
    if ((node as any)._rateStars) {
        return
    }
    (node as any)._rateStars = true;

    const pageId = node.dataset.pageId;

    const number: HTMLElement = node.querySelector('.w-stars-rate-rating .w-stars-rate-number');
    const votes: HTMLElement = node.querySelector('.w-stars-rate-votes .w-stars-rate-number');
    const rateWrapper: HTMLElement = node.querySelector('.w-stars-rate-stars-wrapper');
    const control: HTMLElement = rateWrapper.querySelector('.w-stars-rate-stars-view')
    const cancel: HTMLElement = node.querySelector('.w-stars-rate-cancel');

    let originalRateWidth = control.style.width;
    let rateWith = null;

    const callback = function (votesData) {
        updateRating(number, votes, control, votesData);
        originalRateWidth = control.style.width;
    };

    rateWrapper.addEventListener('mousemove', (e) => {
        const rect = rateWrapper.getBoundingClientRect();
        const total = rect.width;
        const offset = e.clientX - rect.x;
        const value = Math.round(offset / total * 10) / 2;
        control.style.width = `${Math.floor(value * 20)}%`;
        rateWith = value;
    });

    rateWrapper.addEventListener('mouseout', () => {
        control.style.width = originalRateWidth;
    });

    rateWrapper.addEventListener('click', (e) => onClick(e, pageId, rateWith).then(callback));
    cancel.addEventListener('click', (e) => onClick(e, pageId, null).then(callback));
}