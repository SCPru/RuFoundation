/*
 * parsing/rule/impls/block/blocks/tabs.rs
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
use crate::{tree::{AcceptsPartial, PartialElement, Tab}, parsing::string::parse_string};

pub const BLOCK_TABVIEW: BlockRule = BlockRule {
    name: "block-tabview",
    accepts_names: &["tabview", "tabs"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: true,
    accepts_partial: AcceptsPartial::Tab,
    parse_fn: parse_tabview,
};

pub const BLOCK_TAB: BlockRule = BlockRule {
    name: "block-tab",
    accepts_names: &["tab"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: true,
    accepts_partial: AcceptsPartial::None,
    parse_fn: parse_tab,
};

fn parse_tabview<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing tabview block (name '{name}', in-head {in_head})");
    assert!(!flag_star, "Tabview doesn't allow star flag");
    assert!(!flag_score, "Tabview doesn't allow score flag");
    assert_block_name(&BLOCK_TABVIEW, name);

    parser.get_head_none(&BLOCK_TABVIEW, in_head)?;

    let (elements, exceptions, _) =
        parser.get_body_elements(&BLOCK_TABVIEW, name, false)?.into();

    // Build element and return
    let mut tabs = Vec::new();

    for element in elements {
        match element {
            // Append the next tab item.
            Element::Partial(PartialElement::Tab(tab)) => tabs.push(tab),

            // Ignore internal whitespace.
            element if element.is_whitespace() => (),

            // Return a warning for anything else.
            _ => return Err(parser.make_warn(ParseWarningKind::TabViewContainsNonTab)),
        }
    }

    // Ensure it's not empty
    if tabs.is_empty() {
        return Err(parser.make_warn(ParseWarningKind::TabViewEmpty));
    }

    ok!(false; Element::TabView(tabs), exceptions)
}

fn parse_tab<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing tab block (name '{name}', in-head {in_head})");
    assert!(!flag_star, "Tab doesn't allow star flag");
    assert!(!flag_score, "Tab doesn't allow score flag");
    assert_block_name(&BLOCK_TAB, name);

    let mut raw_label =
        parser.get_head_value(&BLOCK_TAB, in_head, |parser, value| match value {
            Some(name) => Ok(name),
            None => Err(parser.make_warn(ParseWarningKind::BlockMissingArguments)),
        })?;

    raw_label = raw_label.trim();

    // hack: Wikidot allows [[tab title=""]]
    // no other arguments are allowed like this. so we just check for tab title
    let label = if raw_label.starts_with("title=\"") && raw_label.ends_with('"') {
        parse_string(&raw_label[6..])
    } else {
        cow!(raw_label)
    };

    let (elements, exceptions, _) = parser.get_body_elements(&BLOCK_TAB, name, true)?.into();

    // Build element and return
    let element = Element::Partial(PartialElement::Tab(Tab {
        label: label,
        elements,
    }));

    ok!(false; element, exceptions)
}
