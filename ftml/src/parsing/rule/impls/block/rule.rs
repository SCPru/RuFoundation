/*
 * parsing/rule/impls/block/rule.rs
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

use crate::parsing::parser::ParserTransactionFlags;

use super::super::prelude::*;
use super::mapping::get_block_rule_with_name;

pub const RULE_BLOCK: Rule = Rule {
    name: "block",
    position: LineRequirement::Any,
    try_consume_fn: block_regular,
};

// Rule implementations

fn block_regular<'r, 't>(
    parser: &mut Parser<'r, 't>,
) -> ParseResult<'r, 't, Elements<'t>> {
    if !parser.settings().enable_block_elements {
        return Err(parser.make_warn(ParseWarningKind::NoRulesMatch))
    }

    info!("Trying to process a block");
    parse_block(parser)
}

// Block parsing implementation

fn parse_block<'r, 't>(parser: &mut Parser<'r, 't>) -> ParseResult<'r, 't, Elements<'t>>
where
    'r: 't,
{
    check_step(parser, Token::LeftBlock, ParseWarningKind::RuleFailed)?;

    // Check star flag
    let flag_star = match parser.current().token {
        Token::BulletItem => {
            parser.step()?;
            true
        },
        _ => false
    };

    info!("Trying to process a block (star {flag_star})");

    // Get block name
    parser.get_optional_space()?;

    let (name, in_head) = parser.get_block_name(flag_star)?;
    debug!("Got block name '{name}' (in head {in_head})");

    let (name, flag_score) = match name.strip_suffix('_') {
        Some(name) => (name, true),
        None => (name, false),
    };

    let (full_name, name) = if name.contains(':') {
        let (short_name, _) = name.split_once(':').unwrap();
        (name, short_name)
    } else {
        (name, name)
    };

    // Get the block rule for this name
    let block = match get_block_rule_with_name(name) {
        Some(block) => block,
        None => return Err(parser.make_warn(ParseWarningKind::NoSuchBlock)),
    };

    // Set block rule for better warnings
    parser.set_block(block);

    // Check if this block allows star invocation (the '[[*' token)
    if !block.accepts_star && flag_star {
        return Err(parser.make_warn(ParseWarningKind::BlockDisallowsStar));
    }

    // Check if this block allows score invocation ('_' after name)
    if !block.accepts_score && flag_score {
        return Err(parser.make_warn(ParseWarningKind::BlockDisallowsScore));
    }

    parser.get_optional_space()?;

    // Run the parse function until the end.
    //
    // This is responsible for parsing any arguments,
    // and terminating the block (the ']]' token),
    // then processing the body (if any) and tail block.
    let parser = &mut parser.transaction(ParserTransactionFlags::AcceptsPartial);
    parser.set_accepts_partial(block.accepts_partial);
    
    let result = (block.parse_fn)(parser, full_name, flag_star, flag_score, in_head)?;

    // If this is an underline block, skip whitespace to next element. This is what Wikidot does.
    // This allows not creating <br> after each <div>
    if flag_score {
        parser.get_optional_spaces_any()?;
    }

    Ok(result)
}
