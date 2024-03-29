/*
 * parsing/rule/impls/list.rs
 *
 * ftml - Library to parse Wikidot text
 * Copyright (C) 2019-2022 Wikijump Team
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

use super::prelude::*;
use crate::parsing::strip::strip_whitespace;
use crate::parsing::{process_depths, DepthItem, DepthList};
use crate::tree::{AttributeMap, ListItem, ListType};

const MAX_LIST_DEPTH: usize = 20;

const fn get_list_type(token: Token) -> Option<ListType> {
    match token {
        Token::BulletItem => Some(ListType::Bullet),
        Token::NumberedItem => Some(ListType::Numbered),
        _ => None,
    }
}

pub const RULE_LIST: Rule = Rule {
    name: "list",
    position: LineRequirement::StartOfLine,
    try_consume_fn,
};

fn try_consume_fn<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
) -> ParseResult<'r, 't, Elements<'t>> {
    // We don't know the list type(s) yet, so just log that we're starting
    info!("Parsing a list");

    // Context variables
    let mut depths = Vec::new();
    let mut exceptions = Vec::new();

    // Blockquotes are always paragraph-unsafe,
    // but we need this binding for chain().
    let mut paragraph_safe = false;

    // Produce a depth list with elements
    loop {
        let current = parser.current();
        let depth = match current.token {
            // Count the number of spaces for its depth
            Token::Whitespace => {
                let spaces = parser.current().slice;

                parser.step()?;

                // Byte count is fine again
                spaces.chars().count()
            }

            // No depth, just the bullet
            Token::BulletItem | Token::NumberedItem => 0,

            // Invalid token, bail
            _ => {
                warn!("Didn't find correct bullet token or couldn't determine list depth, ending list iteration");
                break;
            }
        };

        // Check that the depth isn't obscenely deep, to avoid DOS attacks via stack overflow.
        if depth > MAX_LIST_DEPTH {
            warn!("List item has a depth {depth} greater than the maximum ({MAX_LIST_DEPTH})! Failing");
            return Err(parser.make_warn(ParseWarningKind::ListDepthExceeded));
        }

        // Check that we're processing a bullet, and get the type
        let current = parser.current();
        let list_type = match get_list_type(current.token) {
            Some(ltype) => ltype,
            None => {
                debug!("Didn't find bullet token, couldn't determine list type, ending list iteration");
                break;
            }
        };
        parser.step()?;

        debug!("Parsing list item '{}'", list_type.name());

        // For now, always expect whitespace after the bullet
        let current = parser.current();
        if current.token != Token::Whitespace {
            warn!("Didn't find whitespace after bullet token, ending list iteration");
            break;
        }
        parser.step()?;

        // Parse elements until we hit the end of the line
        let collected_result = collect_consume_keep(
            parser,
            RULE_LIST,
            &[],
            &[
                ParseCondition::current(Token::LineBreak),
                ParseCondition::current(Token::InputEnd),
                ParseCondition::current(Token::ParagraphBreak),
            ],
            &[],
            None,
        )?;

        let should_break = match collected_result.item.1.token {
            Token::LineBreak => false,
            _ => true,
        };

        let mut elements =
            collected_result
                .map(|success| success.0)
                .chain(&mut exceptions, &mut paragraph_safe);

        // Check if depth is empty.
        strip_whitespace(&mut elements);
        
        if !elements.is_empty() {
            // Append list line
            depths.push((depth, list_type, elements));
        }

        if should_break {
            break;
        }
    }

    // This list has no rows, so the rule fails
    if depths.is_empty() {
        return Err(parser.make_warn(ParseWarningKind::RuleFailed));
    }

    let depth_lists = process_depths(ListType::Generic, depths);
    let elements: Vec<Element> = depth_lists
        .into_iter()
        .map(|(ltype, depth_list)| build_list_element(ltype, depth_list))
        .collect();

    ok!(paragraph_safe; elements, exceptions)
}

fn build_list_element(
    top_ltype: ListType,
    list: DepthList<ListType, Vec<Element>>,
) -> Element {
    let mut items = vec![];

    list.into_iter().for_each(|item| return match item {
        DepthItem::Item(elements) => {
            let item = ListItem::Elements {
                hidden: false,
                elements,
                attributes: AttributeMap::new(),
            };
            items.push(item);
        },
        DepthItem::List(ltype, list) => {
            let sub = build_list_element(ltype, list);
            if items.is_empty() {
                items.push(ListItem::Elements {
                    hidden: false,
                    elements: vec![],
                    attributes: AttributeMap::new(),
                });
            }
            match items.last_mut().unwrap() {
                ListItem::Elements { ref mut elements, .. } => {
                    elements.push(sub);
                }
                _ => {}
            }
        },
    });

    // if this list consists of
    let attributes = AttributeMap::new();

    items.iter_mut().for_each(|item| {
        if let ListItem::Elements { ref mut hidden, elements, .. } = item {
            if elements.len() == 1 {
                if let Some(Element::List { .. }) = elements.first() {
                    *hidden = true;
                }
            }
        }
    });

    // Return the Element::List object
    Element::List {
        ltype: top_ltype,
        items,
        attributes,
    }
}
