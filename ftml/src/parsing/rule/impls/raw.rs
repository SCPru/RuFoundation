/*
 * parsing/rule/impls/raw.rs
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

use std::borrow::Cow;

use super::prelude::*;

macro_rules! raw {
    ($value:expr) => {
        Element::Raw(cow!($value))
    };
}

pub const RULE_RAW: Rule = Rule {
    name: "raw",
    position: LineRequirement::Any,
    try_consume_fn,
};

pub const RULE_RAW_HTML: Rule = Rule {
    name: "raw-html",
    position: LineRequirement::Any,
    try_consume_fn: try_consume_html_fn,
};

fn try_consume_fn<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Consuming tokens until end of raw");

    // Check for four special cases:
    // * Raw Raw  "@" -> Element::Raw("@")
    // * Raw Raw !Raw -> Element::Raw("")
    // * Raw Raw  Raw -> Element::Raw("@@")
    // * Raw ??   Raw -> Element::Raw(slice)
    debug!("First token is '@@', checking for special cases");

    // Get next two tokens. If they don't exist, exit early
    let next_1 = parser.look_ahead_warn(0)?;
    let next_2 = parser.look_ahead_warn(1)?;

    // Determine which case they fall under
    match (next_1.token, next_2.token) {
        // "@@@@@@" -> Element::Raw("@@")
        (Token::Raw, Token::Raw) => {
            debug!("Found meta-raw (\"@@@@@@\"), returning");
            parser.step_n(3)?;
            return ok!(raw!("@@"));
        }

        // "@@@@@" -> Element::Raw("@")
        // This case is strange since the lexer returns Raw Raw Other (@@ @@ @)
        // So we capture this and return the intended output
        (Token::Raw, Token::Other) => {
            if next_2.slice == "@" {
                debug!("Found single-raw (\"@@@@@\"), returning");
                parser.step_n(3)?;
                return ok!(raw!("@"));
            } else {
                debug!("Found empty raw (\"@@@@\"), followed by other text");
                parser.step_n(2)?;
                return ok!(raw!(""));
            }
        }

        // "@@@@" -> Element::Raw("")
        // Only consumes two tokens.
        (Token::Raw, _) => {
            debug!("Found empty raw (\"@@@@\"), returning");
            parser.step_n(2)?;
            return ok!(raw!(""));
        }

        // "@@ \n @@" -> Abort
        (Token::ParagraphBreak, Token::Raw) => {
            debug!("Found interrupted raw, aborting");
            return Err(parser.make_warn(ParseWarningKind::RuleFailed));
        }

        // "@@ [something] @@" -> Element::Raw(token)
        (_, Token::Raw) => {
            debug!("Found single-element raw, returning");
            parser.step_n(3)?;
            return ok!(raw!(next_1.slice));
        }

        // Other, proceed with rule logic
        (_, _) => (),
    }

    // Handle the other case:
    // * "@@ [tokens] @@"
    //
    // Collect the first and last token to build a slice of its contents.
    // The last will be updated with each step in the iterator.

    let (start, mut end) = {
        let current = parser.step()?;

        (current, current)
    };

    loop {
        let ExtractedToken {
            token,
            slice: _slice,
            span: _span,
        } = parser.current();

        debug!("Received token '{}' inside raw", token.name());

        // Check token
        match token {
            // Possibly hit end of raw. If not, continue.
            Token::Raw => {
                // If block is inside match rule for clarity
                trace!("Reached end of raw, returning");

                let slice = parser.full_text().slice_partial(start, end);
                parser.step()?;

                let element = Element::Raw(cow!(slice));
                return ok!(element);
            }

            // Hit a newline, abort
            Token::ParagraphBreak => {
                trace!("Reached newline, aborting");
                return Err(parser.make_warn(ParseWarningKind::RuleFailed));
            }

            // Hit the end of the input, abort
            Token::InputEnd => {
                trace!("Reached end of input, aborting");
                return Err(parser.make_warn(ParseWarningKind::EndOfInput));
            }

            // No special handling, append to slices like normal
            _ => (),
        }

        trace!("Appending present token to raw");

        // Update last token and step.
        end = parser.step()?;
    }
}

fn try_consume_html_fn<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Consuming tokens until end of HTML raw");

    parser.step()?;

    let mut elements = Vec::new();
    let mut last_position = parser.current().span.start;

    loop {
        let ExtractedToken {
            token,
            slice,
            span,
        } = parser.current();

        match token {
            Token::RightRaw => {
                // Possibly add more slices to the elements
                if last_position != span.start {
                    elements.push(text!(parser.full_text().slice_indices(last_position, span.start)));
                }
                parser.step()?;
                break
            }

            Token::LineBreak | Token::ParagraphBreak | Token::InputEnd => {
                return Err(parser.make_warn(ParseWarningKind::RuleFailed));
            }

            Token::HtmlEntity => {
                // do not do anything yet
                if last_position != span.start {
                    elements.push(text!(parser.full_text().slice_indices(last_position, span.start)));
                }
                elements.push(Element::HtmlEntity(Cow::from(*slice)));
                last_position = span.end;
            }

            _ => {}
        }

        parser.step()?;
    }

    ok!(true; elements, vec![])
}