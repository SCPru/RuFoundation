/*
 * parsing/rule/impls/block/blocks/char.rs
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
use entities::ENTITIES;
use std::borrow::Cow;
use std::char;
use std::collections::HashMap;

lazy_static! {
    static ref ENTITY_MAPPING: HashMap<&'static str, &'static str> = {
        let mut mapping = HashMap::new();

        for entity in &ENTITIES {
            let key = strip_entity(entity.entity);
            let value = entity.characters;

            mapping.insert(key, value);
        }

        mapping
    };
}

pub const BLOCK_CHAR: BlockRule = BlockRule {
    name: "block-char",
    accepts_names: &["char", "character"],
    accepts_star: false,
    accepts_score: false,
    accepts_newlines: false,
    accepts_partial: AcceptsPartial::None,
    parse_fn,
};

fn parse_fn<'r, 't>(
    parser: &mut Parser<'r, 't>,
    name: &'t str,
    flag_star: bool,
    flag_score: bool,
    in_head: bool,
) -> ParseResult<'r, 't, Elements<'t>> {
    info!("Parsing character / HTML entity block (in-head {in_head})");
    assert!(!flag_star, "Char doesn't allow star flag");
    assert!(!flag_score, "Char doesn't allow score flag");
    assert_block_name(&BLOCK_CHAR, name);

    // Parse the entity and get the string
    let mut string = parser.get_head_value(&BLOCK_CHAR, in_head, parse_entity)?;

    parser.replace_variables(string.to_mut());

    ok!(Element::Text(string))
}

fn parse_entity<'r, 't>(
    parser: &Parser<'r, 't>,
    argument: Option<&'t str>,
) -> Result<Cow<'t, str>, ParseWarning> {
    let argument = match argument {
        Some(arg) => strip_entity(arg),
        None => return Err(parser.make_warn(ParseWarningKind::BlockMissingArguments)),
    };

    match find_entity(argument) {
        Some(string) => Ok(string),
        None => Err(parser.make_warn(ParseWarningKind::BlockMalformedArguments)),
    }
}

/// Find the string corresponding to the passed entity, if any.
fn find_entity(entity: &str) -> Option<Cow<str>> {
    // Named entity
    if let Some(result) = ENTITY_MAPPING.get(entity) {
        return Some(cow!(result));
    }

    // Hexadecimal entity
    if let Some(value) = entity.strip_prefix("#x") {
        if let Some(result) = get_char(value, 16) {
            return Some(result);
        }
    }

    // Decimal entity
    if let Some(value) = entity.strip_prefix('#') {
        if let Some(result) = get_char(value, 10) {
            return Some(result);
        }
    }

    // Not found
    None
}

/// Gets the appropriate character from the number specified in the string.
///
/// Using the passed radix, it gets the integer value, then finds the appropriate
/// character, if one exists.
///
/// Then converts the character into a string with only that value.
fn get_char(value: &str, radix: u32) -> Option<Cow<str>> {
    let codepoint = match u32::from_str_radix(value, radix) {
        Ok(codepoint) => codepoint,
        Err(_) => return None,
    };

    let ch = match char::from_u32(codepoint) {
        Some(ch) => ch,
        None => return None,
    };

    Some(Cow::Owned(ch.to_string()))
}

/// If a string starts with `&` or ends with `;`, those are removed.
/// First trims the string of whitespace.
fn strip_entity(mut s: &str) -> &str {
    s = s.trim();

    if let Some(stripped) = s.strip_prefix('&') {
        s = stripped;
    }

    if let Some(stripped) = s.strip_suffix(';') {
        s = stripped;
    }

    s
}