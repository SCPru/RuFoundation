/*
 * parsing/rule/impls/blockquote.rs
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
use crate::tree::{AttributeMap, Container, ContainerType};

pub const RULE_BLOCKQUOTE: Rule = Rule {
    name: "blockquote",
    position: LineRequirement::StartOfLine,
    try_consume_fn,
};

fn try_consume_fn<'p, 'r, 't>(
    parser: &'p mut Parser<'r, 't>,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing nested native blockquotes");

    // Context variables
    let mut tokens = Vec::new();
    let exceptions = Vec::new();

    // Collect tokens inside this blockquote level.
    loop {
        match parser.current().token {
            Token::Quote => {}
            _ => break
        }
        // read all tokens until newline.
        // after that, append the newline to tokens as well
        parser.step()?;
        // if next token is whitespace, step over it. next token might be `>`, in which case we just ignore
        match parser.current().token {
            Token::Whitespace => {
                parser.step()?;
            }
            _ => {}
        }
        loop {
            tokens.push(parser.current().clone());
            parser.step()?;
            match parser.current().token {
                Token::LineBreak | Token::ParagraphBreak => {
                    tokens.push(parser.current().clone());
                    parser.step()?;
                    break
                }
                Token::InputEnd => break,
                _ => {}
            }
        }
    }

    // tokens must contain the list of tokens inside the blockquote, as if it was separate source.
    let elements = parser.sub_parse(tokens);

    let result = Element::Container(Container::new(
        ContainerType::Blockquote,
        elements,
        AttributeMap::new(),
    ));

    ok!(false; vec![result], exceptions)
}
