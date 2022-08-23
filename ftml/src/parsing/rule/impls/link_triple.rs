/*
 * parsing/rule/impls/link_triple.rs
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

//! Rules for triple-bracket links.
//!
//! This method of designating links is for local pages.
//! The syntax here uses a pipe to separate the destination from the label.
//! However, this method also works for regular URLs, for some reason.
//!
//! Wikidot, in its infinite wisdom, has two means for designating links.
//! This method allows any URL, either opening in a new tab or not.
//! Its syntax is `[[[page-name | Label text]`.

use super::prelude::*;
use crate::{tree::{AnchorTarget, LinkLabel, LinkLocation}, url::validate_href};
use std::borrow::Cow;

pub const RULE_LINK_TRIPLE: Rule = Rule {
    name: "link-triple",
    position: LineRequirement::Any,
    try_consume_fn: link,
};

fn link<'p, 'r, 't>(parser: &'p mut Parser<'r, 't>) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Trying to create a triple-bracket link (regular)");
    check_step(parser, Token::LeftLink, ParseWarningKind::RuleFailed)?;
    try_consume_link(parser, RULE_LINK_TRIPLE)
}

/// Build a triple-bracket link with the given target.
fn try_consume_link<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
    rule: Rule
) -> ParseResult<'r, 't, Elements<'t>> {
    debug!("Trying to create a triple-bracket link");

    // Gather path for link
    let (collected_url, last) = collect_text_keep(
        parser,
        rule,
        &[],
        &[
            ParseCondition::current(Token::Pipe),
            ParseCondition::current(Token::RightLink),
        ],
        &[
            ParseCondition::current(Token::ParagraphBreak),
            ParseCondition::current(Token::LineBreak),
        ],
        None,
    )?;

    let (url, target) = if collected_url.starts_with('*') {
        (&collected_url[1..], Some(AnchorTarget::NewTab))
    } else {
        (collected_url, None)
    };

    debug!("Retrieved url for link, now build element (url: '{url}')");

    // Trim text
    let url = url.trim();

    // If url is an empty string, parsing should fail, there's nothing here
    if url.is_empty() {
        return Err(parser.make_warn(ParseWarningKind::RuleFailed));
    }

    // Determine what token we ended on, i.e. which [[[ variant it is.
    match last.token {
        // [[[name]]] type links
        Token::RightLink => build_same(parser, url, target),

        // [[[url|label]]] type links
        Token::Pipe => build_separate(parser, rule, url, target),

        // Token was already checked in collect_text(), impossible case
        _ => unreachable!(),
    }
}

/// Helper to build link with the same URL and label.
/// e.g. `[[[name]]]`
fn build_same<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
    url: &'t str,
    target: Option<AnchorTarget>,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Building link with same URL and label (url '{url}')");

    // Remove category, if present
    let label = Some(Cow::from(strip_category(url)));

    // Parse out link location
    let (link, ltype) = match LinkLocation::parse_interwiki(cow!(url), parser.settings(), parser.page_callbacks())
    {
        Some(result) => result,
        None => return Err(parser.make_warn(ParseWarningKind::RuleFailed)),
    };

    match &link {
        LinkLocation::Page(page_ref, _) if page_ref.site.is_none() => {
            parser.push_internal_link(page_ref.to_owned());
        },
        LinkLocation::Url(url) => {
            if !validate_href(url, true) {
                return Err(parser.make_warn(ParseWarningKind::RuleFailed));
            }
        },
        _ => return Err(parser.make_warn(ParseWarningKind::CrossSiteRef)),
    }

    // Build and return element
    let element = Element::Link {
        ltype,
        link,
        label: LinkLabel::Url(label),
        target,
    };

    ok!(element)
}

/// Helper to build link with separate URL and label.
/// e.g. `[[[page|label]]]`, or `[[[page|]]]`
fn build_separate<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
    rule: Rule,
    url: &'t str,
    target: Option<AnchorTarget>,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Building link with separate URL and label (url '{url}')");

    // Gather label for link
    let label = collect_text(
        parser,
        rule,
        &[],
        &[ParseCondition::current(Token::RightLink)],
        &[
            ParseCondition::current(Token::ParagraphBreak),
            ParseCondition::current(Token::LineBreak),
        ],
        None,
    )?;

    debug!("Retrieved label for link, now building element (label '{label}')");

    // Trim label
    let label = label.trim();

    // If label is empty, then it takes on the page's title
    // Otherwise, use the label
    let label = if label.is_empty() {
        LinkLabel::Page
    } else {
        LinkLabel::Text(cow!(label))
    };

    // Parse out link location
    let (link, ltype) = match LinkLocation::parse_interwiki(cow!(url), parser.settings(), parser.page_callbacks())
    {
        Some(result) => result,
        None => return Err(parser.make_warn(ParseWarningKind::RuleFailed)),
    };

    match &link {
        LinkLocation::Page(page_ref, _) => {
            parser.push_internal_link(page_ref.to_owned());
        },
        LinkLocation::Url(url) => {
            if !validate_href(url, true) {
                return Err(parser.make_warn(ParseWarningKind::RuleFailed));
            }
        }
    }

    // Build link element
    let element = Element::Link {
        ltype,
        link,
        label,
        target,
    };

    // Return result
    ok!(element)
}

/// Strip off the category for use in URL triple-bracket links.
///
/// The label for a URL link is its URL, but without its category.
/// For instance, `theme: Sigma-9` becomes just `Sigma-9`.
///
/// It returns `Some(_)` if a slice was performed, and `None` if
/// the string would have been returned as-is.
fn strip_category(url: &str) -> &str {
    match url.find(':') {
        // Link with site, e.g. :scp-wiki:component:image-block.
        Some(0) => {
            let url = &url[1..];

            // If there is no colon, it's malformed, return None.
            // Else, return a stripped version
            match url.find(':') {
                Some(idx) => {
                    let url = url[idx + 1..].trim_start();

                    // Skip past the site portion, then use the regular strip case.
                    //
                    // We unwrap_or() here because, at minimum, we return the substring
                    // not containing the site.
                    strip_category(&url)
                }
                None => url
            }
        }

        // Link with category but no site, e.g. theme:sigma-9.
        Some(idx) => url[idx + 1..].trim_start(),

        // No stripping necessary
        None => url,
    }
}

#[test]
fn test_strip_category() {
    macro_rules! check {
        ($input:expr, $expected:expr $(,)?) => {{
            let actual = strip_category($input);

            assert_eq!(
                actual, $expected,
                "Actual stripped URL label doesn't match expected",
            );
        }};
    }

    check!("", "");
    check!("scp-001", "scp-001");
    check!("Guide Hub", "Guide Hub");
    check!("theme:just-girly-things", "just-girly-things");
    check!("theme: just-girly-things", "just-girly-things");
    check!("theme: Just Girly Things", "Just Girly Things");
    check!("component:fancy-sidebar", "fancy-sidebar");
    check!("component:Fancy Sidebar", "Fancy Sidebar");
    check!("component: Fancy Sidebar", "Fancy Sidebar");
    check!(
        "multiple:categories:here:test",
        "categories:here:test",
    );
    check!(
        "multiple: categories: here: test",
        "categories: here: test",
    );
    check!(":scp-wiki:scp-001", "scp-001");
    check!(":scp-wiki : SCP-001", "SCP-001");
    check!(":scp-wiki:system:recent-changes", "recent-changes");
    check!(
        ":scp-wiki : system : Recent Changes",
        "Recent Changes",
    );
    check!(": snippets : redirect", "redirect");
    check!(":", ":");
}
