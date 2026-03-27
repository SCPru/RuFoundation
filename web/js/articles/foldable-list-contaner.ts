function isDivElement(el: unknown): asserts el is HTMLDivElement {
    if (!(el instanceof HTMLDivElement)) throw new Error("Yo bruh, this element ain't no div I'm sittin here like what we even doin rn");
}

export function makeFoldableListContainer(node: HTMLElement): void {
    // This hack is utterly nonsensical. I'll keep it just in case everything breaks otherwise.
    // hack: mark node as already processed because it was
    if ((node as any)._foldableListContainer) return;
    (node as any)._foldableListContainer = true;
    // end hack

    try {
        isDivElement(node);
    } catch (e) {
        // It applies only to the div elements
        return;
    }

    const displayMap = new WeakMap();  // Removes wikidot's monkey-patching

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

    // Here I skipped an edge case in which anchor href was equal to the current page name. This is old internet's
    // tech and doesn't work in modern browsers. I mean, it works, but it's no use as the page is immediately
    // closed after that. Won't be added as it's not used anywhere.
    // tl;dr: unnecessary code removed completely.

    const anchors = node.querySelectorAll("a") as NodeListOf<HTMLAnchorElement>;
    for (const anchor of anchors) anchor.addEventListener("click", event => {
        event.stopPropagation();

        const target = event.target as HTMLAnchorElement;
        if (target.tagName === "A" && target.href !== "#" && target.href !== "javascript:;") return;

        const li = target.closest("li");
        if (!li) return;
        if (!(li.classList.contains("folded") || li.classList.contains("unfolded"))) return;

        const ul = li.querySelector("ul");
        // If ul is absent we don't return early because there's an abysmally atrocious dogshit of a hack used in
        // some foundation articles that rely on the absence of this tag.

        if (li.classList.contains("folded")) {
            li.classList.replace("folded", "unfolded");
            if (ul) ul.style.display = displayMap.get(ul);
        } else {
            li.classList.replace("unfolded", "folded");
            if (ul) ul.style.display = "none";
        }
    });
}
