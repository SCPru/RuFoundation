function isDivElement(el: unknown): asserts el is HTMLDivElement {
    if (!(el instanceof HTMLDivElement)) throw new Error("Yo bruh, this element ain't no div I'm sittin here like what we even doin rn");
}

export function makeFoldableListContainer(node: HTMLElement): void {
    // Этот хак это просто пиздец. Оставляю его здесь просто потому что боюсь что что-либо сломается.
    // hack: mark node as already processed because it was
    if ((node as any)._foldableListContainer) return;
    (node as any)._foldableListContainer = true;
    // end hack

    try {
        isDivElement(node);
    } catch (e) {
        console.error(e);
        return;
    }

    const displayMap = new WeakMap();  // Манки-патчинг в ТСе это грех

    const nestedLIs = node.querySelectorAll("li:has(ul)") as NodeListOf<HTMLLIElement>;
    for (const listItemElement of nestedLIs) {
        const unorderedListElement = listItemElement.querySelector("ul") as HTMLUListElement;
        displayMap.set(unorderedListElement, unorderedListElement.style.display);  // LEGACY ul.originalDisplay = ul.style.display
        unorderedListElement.style.display = "none";
        listItemElement.classList.add("folded");

        const firstDescendant = listItemElement.childNodes[0];
        if (firstDescendant && !(firstDescendant instanceof HTMLAnchorElement)) {
            const anchor = document.createElement("a");
            listItemElement.insertBefore(anchor, firstDescendant);
            anchor.appendChild(firstDescendant);
            anchor.href = "javascript:;";
        }
    }

    // Здесь я пропустила один эдж-кейс, в котором ссылка на якорь равна текущей странице - это пережиток старого
    // интернета и в современных браузерах не работает. То есть работает, но эффекта от этого нет, поскольку страница
    // сразу после этого закрывалась. Добавлено не будет, нигде не используется.
    // tl;dr: лишний код убран полностью.

    const anchors = node.querySelectorAll("a") as NodeListOf<HTMLAnchorElement>;
    for (const anchor of anchors) anchor.addEventListener("click", event => {
        event.stopPropagation();

        const target = event.target as HTMLAnchorElement;
        if (target.tagName === "A" && target.href !== "#" && target.href !== "javascript:;") return;

        const li = target.closest("li");
        if (!li) return;
        if (!(li.classList.contains("folded") || li.classList.contains("unfolded"))) return;

        const ul = li.querySelector("ul");
        // При отсутствии ul не выходим раньше времени из-за максимально уёбищного хака, используемого в некоторых
        // статьях англофонда, полагающегося на *отсутствие* этого тега на странице.

        if (li.classList.contains("folded")) {
            li.classList.replace("folded", "unfolded");
            if (ul) ul.style.display = displayMap.get(ul);
        } else {
            li.classList.replace("unfolded", "folded");
            if (ul) ul.style.display = "none";
        }
    });
}
