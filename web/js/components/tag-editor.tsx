import * as React from 'react';
import styled from 'styled-components';
import {FetchAllTagsResponse} from '../api/tags';
import {useRef, useState} from 'react'

interface Props {
    tags: Array<string>
    allTags: FetchAllTagsResponse
    onChange?: (tags: Array<string>) => void
    canCreateTags?: boolean
}

const TagEditorContainer = styled.div`
  * {
    box-sizing: border-box;
  }
`


const TagListContainer = styled.div`
  width: 100%;
  display: grid;
  grid-template-columns: min-content 1fr;
  
  @media (max-width: 500px) {
    grid-template-columns: 1fr;
  }
`

const TagCategoryName = styled.div`
  &:after {
    content: ':';
  }
  
  font-weight: 600;
  margin-right: 8px;
  padding: 2px 0;
  margin-bottom: 4px;
  white-space: nowrap;
`

const TagList = styled.div`
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  margin: -2px;
  margin-bottom: 4px;
`

const Tag = styled.div`
  white-space: nowrap;
  background: #eee;
  border-radius: 4px;
  margin: 2px;
  padding: 2px 4px;
  padding-right: 0;
  display: flex;
`

const TagDelete = styled.div`
  cursor: pointer;
  margin-left: 4px;
  border-left: 1px solid #aaa;
  padding: 0 4px;
  margin-right: 2px;
  border-radius: 0 2px 2px 0;
  
  &:hover {
    background: #eaa;
  }
  
  &:after {
    content: '×';
  }
`

const TagInputArea = styled.div`
  height: 300px;
  max-height: 300px;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
`

const TagInputTitle = styled.div`
  margin-bottom: 4px;
  font: inherit;
`

const TagInput = styled.input`
  width: 100%;
`

const TagSuggestionList = styled.div`
  border: 1px solid #ccc;
  border-top: 0;
  width: 100%;
  overflow-y: auto;
`

const TagSuggestionCategory = styled.div`
  padding: 4px 8px;
  background: #eee;
  font-weight: 600;
  border-bottom: 1px solid #aaa;
  cursor: pointer;
  &:last-child {
    border-bottom: 0;
  }
  &:hover, &.active {
    background: #263636;
    color: white;
  }
`

const TagSuggestionTag = styled.div`
  padding: 4px 8px;
  border-bottom: 1px solid #aaa;
  cursor: pointer;
  &:last-child {
    border-bottom: 0;
  }
  &:hover, &.active {
    background: #446060;
    color: white;
  }
`


const TagEditorComponent: React.FC<Props> = ({ tags, allTags, onChange, canCreateTags }) => {
    const [inputValue, setInputValue] = useState('')
    const [suggestionsOpen, setSuggestionsOpen] = useState(false)
    const [selectedToAdd, setSelectedToAdd] = useState<string>()
    const inputRef = useRef<HTMLInputElement>()
    const suggestionsRef = useRef<HTMLDivElement>()

    const parsedTags = tags.map(tag => {
        const categoryAndName = tag.split(':', 2);
        if (categoryAndName.length === 1) {
            categoryAndName.splice(0, 0, '_default');
        }
        const [category, name] = categoryAndName;
        return { category, name, fullName: tag };
    });

    const categoriesAndTags = allTags.categories.map(category => {
        return {
            name: category.name,
            slug: category.slug,
            tags: parsedTags.filter(x => x.category.toLowerCase() === category.slug.toLowerCase())
        };
    }).filter(x => !!x.tags.length);

    parsedTags.forEach(tag => {
        if (!allTags.categories.find(x => x.slug.toLowerCase() === tag.category.toLowerCase())) {
            let category = categoriesAndTags.find(x => x.slug.toLowerCase() === tag.category.toLocaleLowerCase());
            if (!category) {
                category = {
                    name: tag.category,
                    slug: tag.category,
                    tags: []
                };
                categoriesAndTags.push(category);
            }
            category.tags.push(tag);
        }
    });

    const filteredCategories = allTags.categories.map(category => ({
            ...category,
            tags: allTags.tags.filter(x => x.categoryId === category.id)
        }))
        .map(category => ({
            ...category,
            tags: (category.slug.toLowerCase().indexOf(inputValue.toLowerCase()) !== -1 || `${category.slug.toLowerCase()}:` === inputValue)
                ? category.tags
                : category.tags.filter(x => !tags.find(y => y.toLowerCase() === `${category.slug}:${x.name}`.toLowerCase()) && x.name.toLowerCase().indexOf(inputValue.toLowerCase()) !== -1)
        })).filter(x => !!x.tags.length)

    const onDeleteTag = (e: React.MouseEvent, tag: string) => {
        e.preventDefault();
        e.stopPropagation();

        if (!onChange) {
            return;
        }

        onChange(tags.filter(x => x.toLowerCase() !== tag.toLowerCase()));
    };

    const onInputChange = (e: React.ChangeEvent) => {
        const value = (e.target as HTMLInputElement).value;
        if (value.length <= 1) {
            setSelectedToAdd(undefined);
            if (!value.length) {
                setSuggestionsOpen(false);
            }
        }
        if (value.length) {
            setSuggestionsOpen(true);
        }
        setInputValue(value);
    };

    const onInputFocus = () => {
        setSuggestionsOpen(true);
    };

    const onSelectCategory = (e: React.MouseEvent, category: string) => {
        e.preventDefault();
        e.stopPropagation();
        setInputValue(`${category}:`);
    };

    const onSelectTag = (e: React.MouseEvent, tag: string) => {
        e.preventDefault();
        e.stopPropagation();

        if (!onChange) {
            return;
        }

        setInputValue('');
        onChange([...tags.filter(x => x.toLowerCase() !== tag.toLowerCase()), tag]);
    };

    const onInputBlur = (e: React.FocusEvent) => {
        let p: Node = e.relatedTarget as Node;
        while (p) {
            if (p === inputRef.current || p === suggestionsRef.current) {
                return;
            }
            p = p.parentNode;
        }
        setTimeout(() => setSuggestionsOpen(false), 100);
    };

    const onInputKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && canCreateTags) {
            setInputValue('');
            onChange([...tags.filter(x => x.toLowerCase() !== inputValue.toLowerCase()), inputValue]);
            e.preventDefault();
            e.stopPropagation();
        }
    };

    return (
        <TagEditorContainer>
            <TagListContainer>
                {categoriesAndTags.map(category => (
                    <React.Fragment key={category.name}>
                        <TagCategoryName>
                            {category.name}
                        </TagCategoryName>
                        <TagList>
                            {category.tags.map(tag => (
                                <Tag key={tag.name}>
                                    {tag.name}
                                    <TagDelete onClick={e => onDeleteTag(e, tag.fullName)} />
                                </Tag>
                            ))}
                        </TagList>
                    </React.Fragment>
                ))}
            </TagListContainer>
            <TagInputArea>
                <TagInputTitle>
                    Добавить тег:<br/>
                    (начните печатать для поиска по тегам)
                </TagInputTitle>
                <TagInput onChange={onInputChange} type="text" value={inputValue} onFocus={onInputFocus} onBlur={onInputBlur} ref={inputRef} onKeyDown={onInputKeyDown} />
                {!!inputValue.trim().length && !!filteredCategories.length && suggestionsOpen && (
                    <TagSuggestionList ref={suggestionsRef}>
                        {filteredCategories.map(category => (
                            <React.Fragment key={category.slug}>
                                <TagSuggestionCategory className={selectedToAdd === `${category.slug}:` ? 'active' : ''} onClick={e => onSelectCategory(e, category.slug)}>
                                    {category.name} [{category.slug}]
                                </TagSuggestionCategory>
                                {category.tags.map(tag => (
                                    <TagSuggestionTag key={tag.name} className={selectedToAdd === `${category.slug}:${tag.name}` ? 'active' : ''} onClick={e => onSelectTag(e, `${category.slug}:${tag.name}`)}>
                                        {tag.name}
                                    </TagSuggestionTag>
                                ))}
                            </React.Fragment>
                        ))}
                    </TagSuggestionList>
                )}
            </TagInputArea>
        </TagEditorContainer>
    )
}


export default TagEditorComponent;