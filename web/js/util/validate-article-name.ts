function getName(fullName: string) {
    const split = fullName.indexOf(':')

    if (split === -1) return { category: '_default', name: fullName }
    else return { category: fullName.substring(0, split), name: fullName.substring(split + 1) }
}

export function isFullNameAllowed(articleName: string) {
    const reserved = ['-', '_', 'api', 'forum', 'local--files', 'local--code'];
    
    articleName = articleName.toLowerCase();
    if (reserved.includes(articleName)  || 
        articleName.length > 128        ||
        !/^[A-Za-z0-9\-_:]+$/.test(articleName))
        return false;

    const { category, name } = getName(articleName);

    if (!category.trim() || !name.trim()) return false;
    return true;
}