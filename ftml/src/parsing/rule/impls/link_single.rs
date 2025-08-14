/*
 * parsing/rule/impls/link_single.rs
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

//! Rules for single-bracket links.
//!
//! Wikidot, in its infinite wisdom, has two means for designating links.
//! This method allows any URL, either opening in a new tab or not.
//! Its syntax is `[https://example.com/ Label text]`.

use super::prelude::*;
use crate::tree::{AnchorTarget, LinkLabel, LinkLocation, LinkType};
use crate::url::validate_href;

pub const RULE_LINK_SINGLE: Rule = Rule {
    name: "link-single",
    position: LineRequirement::Any,
    try_consume_fn: link,
};

fn link<'p, 'r, 't>(parser: &'p mut Parser<'r, 't>) -> ParseResult<'r, 't, Elements<'t>> {
    debug!("Trying to create a single-bracket link (regular)");
    check_step(parser, Token::LeftBracket, ParseWarningKind::RuleFailed)?;
    try_consume_link(parser, RULE_LINK_SINGLE)
}

/// Build a single-bracket link with the given target.
fn try_consume_link<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
    rule: Rule
) -> ParseResult<'r, 't, Elements<'t>> {
    info!(
        "Trying to create a single-bracket link"
    );

    // Gather path for link
    let collected_url = collect_text(
        parser,
        rule,
        &[],
        &[ParseCondition::current(Token::Whitespace)],
        &[
            ParseCondition::current(Token::RightBracket),
            ParseCondition::current(Token::ParagraphBreak),
            ParseCondition::current(Token::LineBreak),
        ],
        None,
    )?;

    let (mut url, target) = if collected_url.starts_with('*') {
        (&collected_url[1..], Some(AnchorTarget::NewTab))
    } else {
        (collected_url, None)
    };

    // Return error if the resultant URL is not valid.
    if !validate_href(url, true) {
        return Err(parser.make_warn(ParseWarningKind::InvalidUrl));
    }

    // Hack for Wikidot compatibility: [# link] on Wikidot becomes javascript:;
    if url == "#" {
        url = "javascript:;";
    }

    let ltype = if url.starts_with('#') {
        LinkType::Anchor
    } else {
        LinkType::Direct
    };

    debug!("Retrieved URL '{url}' for link, now fetching label");

    // Gather label for link
    let label = collect_text(
        parser,
        rule,
        &[],
        &[ParseCondition::current(Token::RightBracket)],
        &[
            ParseCondition::current(Token::ParagraphBreak),
            ParseCondition::current(Token::LineBreak),
        ],
        None,
    )?;

    debug!("Retrieved label for link, now build element (label '{label}')");

    // Trim label
    let label = label.trim();

    // Build link element
    let element = Element::Link {
        ltype,
        link: LinkLocation::Url(cow!(url)),
        label: LinkLabel::Text(cow!(label)),
        target,
    };

    // Return result
    ok!(element)
}
